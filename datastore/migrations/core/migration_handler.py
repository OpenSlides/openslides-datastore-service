from enum import Enum
from typing import Any, Dict, Protocol, Type

from datastore.shared.di import service_as_factory, service_interface
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.util import KEYSEPARATOR, InvalidDatastoreState

from .base_migrations.base_migration import BaseMigration
from .exceptions import MigrationSetupException, MismatchingMigrationIndicesException
from .migraters.interface import EventMigrater
from .migration_keyframes import DatabaseMigrationKeyframeModifier
from .migration_logger import MigrationLogger


class MigrationState(str, Enum):
    NO_MIGRATION_REQUIRED = "no_migration_required"
    FINALIZATION_REQUIRED = "finalization_required"
    MIGRATION_REQUIRED = "migration_required"


@service_interface
class MigrationHandler(Protocol):
    def register_migrations(self, *migrations: Type[BaseMigration]) -> None:
        """
        Provide the class objects of all migrations to run. It is checked, that they
        have the right target_migration_index set.
        """

    def migrate(self) -> None:
        """
        Run migrations. They are not finalized, so additional migrations (and positions)
        can be executed later on.
        """

    def finalize(self) -> None:
        """
        Run migrations and finalize them.
        """

    def reset(self) -> None:
        """
        Remove all not-finalized migration data. `migrate` and `reset` in combination
        is some kind of dry-run of the migrations.
        """

    def delete_collectionfield_aux_tables(self) -> None:
        """
        Clears the collectionfield tables.
        """

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns a dict with some useful stats about the migration state.
        """

    def print_stats(self) -> None:
        """
        Prints the dict returned by `get_stats` in a readable way.
        """


@service_as_factory
class MigrationHandlerImplementation(MigrationHandler):
    read_database: ReadDatabase
    connection: ConnectionHandler
    event_migrater: EventMigrater
    logger: MigrationLogger
    target_migration_index: int = 1  # initial index, no migrations to apply

    def __init__(self):
        self.migrations_by_target_migration_index = {}

    def register_migrations(self, *migrations: Type[BaseMigration]) -> None:
        if self.migrations_by_target_migration_index:
            raise MigrationSetupException("Already registered some migrations!")

        _migrations = [migration() for migration in migrations]  # instantiate
        _migrations.sort(key=lambda x: x.target_migration_index)
        for i, migration in enumerate(_migrations):
            if migration.target_migration_index != i + 2:
                raise MigrationSetupException(
                    "target_migration_index: Migrations are not numbered sequentially "
                    + f"beginning at 2. Found {migration.name} at position {i+1} and "
                    + f"target_migration_index {migration.target_migration_index}, "
                    + f"expected migration index {i+2}"
                )
            self.migrations_by_target_migration_index[
                migration.target_migration_index
            ] = migration
        self.target_migration_index = len(_migrations) + 1

    def migrate(self) -> None:
        self.logger.info("Running migrations.")
        if self.run_checks():
            return
        if self.run_migrations():
            self.logger.info("Done. Finalizing is still needed.")

    def run_migrations(self) -> bool:
        return self.event_migrater.migrate(
            self.target_migration_index, self.migrations_by_target_migration_index
        )

    def run_checks(self) -> bool:
        with self.connection.get_connection_context():
            if self.check_datastore_empty():
                return True

            self.assert_valid_migration_index()

            if self.check_for_latest():
                return True
        return False

    def check_datastore_empty(self) -> bool:
        if self.read_database.is_empty():
            self.logger.info("Datastore is empty, nothing to do.")
            return True
        return False

    def assert_valid_migration_index(self) -> None:
        # assert untouched db and assert consistent migration index
        self.read_database.reset()
        try:
            max_db_mi = self.read_database.get_current_migration_index()
        except InvalidDatastoreState as e:
            raise MismatchingMigrationIndicesException(str(e))

        max_migrations_mi = (
            self.connection.query_single_value(
                "select max(migration_index) from migration_positions", []
            )
            or 1
        )
        datastore_max_migration_index = max(max_db_mi, max_migrations_mi)

        if datastore_max_migration_index > self.target_migration_index:
            raise MismatchingMigrationIndicesException(
                "The datastore has a higher migration index "
                + f"({datastore_max_migration_index}) than the registered"
                + f" migrations ({self.target_migration_index})"
            )

    def check_for_latest(self) -> bool:
        min_migration_index = (
            self.connection.query_single_value(
                "select min(migration_index) from positions", []
            )
            or 1
        )
        if min_migration_index == -1:
            self._update_migration_index()
            self.connection.execute("delete from migration_events", [])
            self.connection.execute("delete from migration_positions", [])
            self.connection.execute("delete from migration_keyframes", [])
            self.connection.execute("delete from migration_keyframe_models", [])
            self.logger.info(
                f"The datastore has a migration index of -1. Set the migration index to {self.target_migration_index}."
            )
            return True
        return False

    def finalize(self) -> None:
        self.logger.info("Finalize migrations.")
        if self.run_checks():
            self.delete_collectionfield_aux_tables()
            return
        if not self.run_migrations():
            return

        self.delete_collectionfield_aux_tables()

        self.logger.info("Calculate helper tables...")
        with self.connection.get_connection_context():
            self.fill_models_aux_tables()
            self.fill_id_sequences_table()

        self._delete_migration_keyframes()

        self.logger.info("Swap events and migration_events tables...")
        with self.connection.get_connection_context():
            self.connection.execute("alter table events rename to events_swap", [])
            self.connection.execute("alter table migration_events rename to events", [])
            self.connection.execute(
                "alter table events_swap rename to migration_events", []
            )

        self.logger.info(
            f"Set the new migration index to {self.target_migration_index}..."
        )
        with self.connection.get_connection_context():
            self._update_migration_index()

        self._clean_migration_data()

    def reset(self) -> None:
        self.logger.info("Reset migrations.")
        with self.connection.get_connection_context():
            if self.check_datastore_empty():
                return

            self.assert_valid_migration_index()

        self._delete_migration_keyframes()
        self._clean_migration_data()

    def _update_migration_index(self) -> None:
        self.connection.execute(
            "update positions set migration_index=%s",
            [self.target_migration_index],
        )
        # update migration index cache
        self.read_database.reset()

    def _delete_migration_keyframes(self) -> None:
        self.logger.info("Deleting all migration keyframes...")
        with self.connection.get_connection_context():
            self.connection.execute("delete from migration_keyframes", [])
            self.connection.execute("delete from migration_keyframe_models", [])

    def _clean_migration_data(self) -> None:
        self.logger.info("Clean up migration data...")
        with self.connection.get_connection_context():
            self.connection.execute("delete from migration_positions", [])
            self.connection.execute("delete from migration_events", [])
            sequence = self.connection.query_single_value(
                "select pg_get_serial_sequence('migration_events', 'id');", []
            )
            self.connection.execute(f"alter sequence {sequence} restart with 1", [])

    def delete_collectionfield_aux_tables(self) -> None:
        self.logger.info("Cleaning collectionfield helper tables...")
        with self.connection.get_connection_context():
            self.connection.execute("delete from events_to_collectionfields", [])
            self.connection.execute("delete from collectionfields", [])

    def fill_models_aux_tables(self):
        # Use the DatabaseMigrationKeyframeModifier to copy all models into `models`
        max_position = self.connection.query_single_value(
            "select max(position) from positions", []
        )
        keyframe_id = DatabaseMigrationKeyframeModifier.get_keyframe_id(
            self.connection, max_position, self.target_migration_index
        )
        self.connection.execute("delete from models", [])

        self.connection.execute(
            """insert into models (fqid, data, deleted) select fqid, data, deleted
            from migration_keyframe_models where keyframe_id=%s""",
            [keyframe_id],
        )

    def fill_id_sequences_table(self):
        """Rebuild the `id_sequences` table from the models in `models`."""
        self.connection.execute("delete from id_sequences", [])
        self.connection.execute(
            """\
            insert into id_sequences (collection, id)
            select split_part(fqid, %s, 1) as collection,
            max((split_part(fqid, %s, 2))::int) + 1 as id
            from models group by split_part(fqid, %s, 1)
            """,
            [KEYSEPARATOR] * 3,
        )

    def get_stats(self) -> Dict[str, Any]:  # pragma: no cover
        def count(table):
            return (
                self.connection.query_single_value(f"select count(*) from {table}", [])
                or 0
            )

        with self.connection.get_connection_context():
            count_positions = count("positions")
            count_events = count("events")
            current_migration_index = self.read_database.get_current_migration_index()

            count_migration_positions = count("migration_positions")
            count_migration_positions_full = (
                self.connection.query_single_value(
                    "select count(*) from migration_positions where migration_index=%s",
                    [self.target_migration_index],
                )
                or 0
            )
            count_migration_positions_partial = (
                count_migration_positions - count_migration_positions_full
            )

            max_mi_migration_positions = self.connection.query_single_value(
                "select max(migration_index) from migration_positions", []
            )
            if (
                max_mi_migration_positions
                and current_migration_index != max_mi_migration_positions
            ) or current_migration_index != self.target_migration_index:
                if (
                    count_positions == count_migration_positions
                    and max_mi_migration_positions == self.target_migration_index
                ):
                    status = MigrationState.FINALIZATION_REQUIRED
                else:
                    status = MigrationState.MIGRATION_REQUIRED
            else:
                status = MigrationState.NO_MIGRATION_REQUIRED

        return {
            "status": status,
            "current_migration_index": current_migration_index,
            "target_migration_index": self.target_migration_index,
            "positions": count_positions,
            "events": count_events,
            "partially_migrated_positions": count_migration_positions_partial,
            "fully_migrated_positions": count_migration_positions_full,
        }

    def print_stats(self) -> None:  # pragma: no cover
        stats = self.get_stats()
        if stats["current_migration_index"] == stats["target_migration_index"]:
            action = "The datastore is up-to-date"
        else:
            action = "Migration/Finalization is needed"
        if stats["status"] == MigrationState.NO_MIGRATION_REQUIRED:
            migration_action = "No action needed"
        elif stats["status"] == MigrationState.MIGRATION_REQUIRED:
            migration_action = "Migration and finalization needed"
        elif stats["status"] == MigrationState.FINALIZATION_REQUIRED:
            migration_action = "Finalization needed"
        self.logger.info(
            f"""\
- Registered migrations for migration index {self.target_migration_index}
- Datastore has {stats['positions']} positions with {stats['events']} events
- The positions have a migration index of {stats['current_migration_index']}
  -> {action}
- There are {stats['fully_migrated_positions']} fully migrated positions and
  {stats['partially_migrated_positions']} partially migrated ones
  -> {migration_action}
- {stats['positions'] - stats['fully_migrated_positions']} positions have to be migrated (including
  partially migrated ones)"""
        )


class MigrationHandlerImplementationMemory(MigrationHandlerImplementation):
    """
    All migrations are made in-memory only for the import of meetings.
    """

    def finalize(self) -> None:
        self.logger.info("Finalize in memory migrations.")
        self.run_migrations()
        self.logger.info("Finalize in memory migrations ready.")

    def run_migrations(self) -> bool:
        self.event_migrater.migrate(
            self.target_migration_index,
            self.migrations_by_target_migration_index,
        )
        return False
