from typing import Protocol, Type

from datastore.shared.di import service_as_factory, service_interface
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.util import KEYSEPARATOR

from .base_migration import BaseMigration
from .exceptions import MigrationSetupException, MismatchingMigrationIndicesException
from .migrater import Migrater
from .migration_keyframes import DatabaseMigrationKeyframeModifier
from .migration_logger import MigrationLogger


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

    def print_stats(self) -> None:
        """
        Prints some useful stats about the migration state.
        """


@service_as_factory
class MigrationHandlerImplementation:

    connection: ConnectionHandler
    migrater: Migrater
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
            self.logger.info("Done. Finalizing is still be needed.")

    def run_migrations(self) -> bool:
        return self.migrater.migrate(
            self.target_migration_index, self.migrations_by_target_migration_index
        )

    def run_checks(self) -> bool:
        with self.connection.get_connection_context():
            if self.check_datastore_empty():
                return True

            self.assert_not_too_high_migration_index()

            if self.check_for_latest():
                return True
        return False

    def check_datastore_empty(self) -> bool:
        number_of_positions = self.connection.query_single_value(
            "select count(*) from positions", []
        )
        if number_of_positions == 0:
            self.logger.info("Datastore is empty, nothing to do.")
            return True
        return False

    def assert_not_too_high_migration_index(self) -> None:
        # get max migration index from positions and migration_positions
        _max_1 = (
            self.connection.query_single_value(
                "select max(migration_index) from positions", []
            )
            or 1
        )
        _max_2 = (
            self.connection.query_single_value(
                "select max(migration_index) from migration_positions", []
            )
            or 1
        )
        datastore_max_migration_index = max(_max_1, _max_2)

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
            self.connection.execute(
                "update positions set migration_index=%s",
                [self.target_migration_index],
            )
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
            self.connection.execute(
                "update positions set migration_index=%s",
                [self.target_migration_index],
            )

        self._clean_migration_data()

    def reset(self) -> None:
        self.logger.info("Reset migrations.")
        with self.connection.get_connection_context():
            if self.check_datastore_empty():
                return

            self.assert_not_too_high_migration_index()

        self._delete_migration_keyframes()
        self._clean_migration_data()

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

    def print_stats(self) -> None:  # pragma: no cover
        def count(table):
            return (
                self.connection.query_single_value(f"select count(*) from {table}", [])
                or 0
            )

        with self.connection.get_connection_context():
            count_positions = count("positions")
            count_events = count("events")
            min_mi_positions = (
                self.connection.query_single_value(
                    "select min(migration_index) from positions", []
                )
                or 1
            )
            if min_mi_positions == -1:
                self.logger.info(
                    "Minimum migration index of -1 found. Setting the Datastore to "
                    + f"{self.target_migration_index} with the next migrate or finalize."
                )
                return

            max_mi_positions = (
                self.connection.query_single_value(
                    "select max(migration_index) from positions", []
                )
                or 1
            )

            if min_mi_positions != max_mi_positions:
                action = "Error! The position table always must have the same migration index!"
            elif min_mi_positions == self.target_migration_index:
                action = "The Datastore is up-to-date."
            else:
                action = "Migration/Finalization is needed"

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

            max_mi_migration_positions = (
                self.connection.query_single_value(
                    "select max(migration_index) from migration_positions", []
                )
                or 1
            )
            if (
                min_mi_positions != max_mi_migration_positions
                or min_mi_positions != self.target_migration_index
            ):
                if (
                    count_positions == count_migration_positions
                    and max_mi_migration_positions == self.target_migration_index
                ):
                    migration_action = "Finalization needed."
                    positions_to_migrate = 0
                else:
                    migration_action = "Migration and finalization needed."
                    positions_to_migrate = (
                        count_positions - count_migration_positions_full
                    )
            else:
                migration_action = "No action needed."
                positions_to_migrate = 0

        self.logger.info(
            f"""\
- Registered migrations for migration index {self.target_migration_index}
- Datastore has {count_positions} positions with {count_events} events
- The positions have a minimal migration index {min_mi_positions} and a maximal
  migration index {max_mi_positions}
  -> {action}
- There are {count_migration_positions} migration positions: {count_migration_positions_full} fully migrated,
  {count_migration_positions_partial} partial migrated
  -> {migration_action}
- {positions_to_migrate} positions have to be migrated (including partially migrated ones)"""
        )
