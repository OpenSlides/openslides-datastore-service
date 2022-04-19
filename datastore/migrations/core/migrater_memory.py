from datetime import datetime
from typing import Dict, List, Tuple, cast

from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.typing import Fqid, Model, Position

from .base_migration import BaseMigration
from .events import BaseEvent, CreateEvent
from .exceptions import MismatchingMigrationIndicesException
from .migration_keyframes import (
    InitialMigrationKeyframeModifier,
    MigrationKeyframeModifier,
)
from .migration_logger import MigrationLogger
from .migrater import RawPosition


@service_as_factory
class MigraterImplementationMemory:
    read_database: ReadDatabase
    connection: ConnectionHandler
    logger: MigrationLogger
    target_migration_index: int
    import_create_events: List[BaseEvent]
    imported_models: Dict[Fqid, Model]

    def migrate(
        self, target_migration_index: int, migrations: Dict[int, BaseMigration], start_migration_index: int = 0
    ) -> bool:
        self.target_migration_index = target_migration_index
        self.migrations = migrations
        self.start_migration_index = start_migration_index

        if self.start_migration_index == -1 or self.start_migration_index == self.target_migration_index:
            self.logger.info(
                "No migrations to apply for data to import. "
                + f"Given migration index of import data: {self.start_migration_index} "
                + f"Current backend migration index: {self.target_migration_index}"
            )
        elif self.start_migration_index == 0 or start_migration_index > self.target_migration_index:
            raise MismatchingMigrationIndicesException(
                "The migration index of import data is invalid: "
                + f"Given migration index of import data: {self.start_migration_index} "
                + f"Current backend migration index: {self.target_migration_index}"
            )
        else:
            self.run_actual_migrations()

        return False

    def run_actual_migrations(self) -> None:
        position = RawPosition(position=1, migration_index=self.start_migration_index, timestamp=datetime.now(), user_id=0, information=None)
        last_position_value = 0
        self.migrate_position(position, last_position_value)

    def migrate_position(
        self, position: RawPosition, last_position_value: Position
    ) -> None:
        """
        Used for in memory migration of import data.
        All import data will be imported at one position.
        """
        migration_index = position.migration_index

        self.logger.info(
            f"Migrate import data from MI {migration_index} to MI {self.target_migration_index} ..."
        )
        for source_migration_index in range(
            migration_index, self.target_migration_index
        ):
            target_migration_index = source_migration_index + 1
            self.logger.debug(
                f"\tRunning migration with target migration index {target_migration_index}"
            )
            old_accessor, new_accessor = self.get_accessors(
                last_position_value,
                source_migration_index,
                target_migration_index,
                position.position,
                False,
            )

            migration = self.migrations[target_migration_index]

            old_events = self.import_create_events
            new_events = migration.migrate(
                old_events, old_accessor, new_accessor, position.to_position_data()
            )
            self.import_create_events = new_events

    def get_accessors(
        self,
        last_position_value: Position,
        source_migration_index: int,
        target_migration_index: int,
        position: Position,
        is_last_migration_index: bool,
    ) -> Tuple[MigrationKeyframeModifier, MigrationKeyframeModifier]:
        old_accessor = InitialMigrationKeyframeModifier(
            self.connection,
            last_position_value,
            source_migration_index,
            position,
        )
        old_accessor.models.update(self.imported_models)
        old_accessor.deleted.update({key: False for key in self.imported_models})
        new_accessor = InitialMigrationKeyframeModifier(
            self.connection,
            last_position_value,
            target_migration_index,
            position,
        )
        new_accessor.models.update(self.imported_models)
        new_accessor.deleted.update({key: False for key in self.imported_models})
        return old_accessor, new_accessor

    def set_additional_data(self, import_create_events: List[CreateEvent], models: Dict[Fqid, Model]) -> None:
        self.import_create_events = cast(List[BaseEvent], import_create_events)
        self.imported_models = models

    def get_migrated_create_events(self) -> List[BaseEvent]:
        return self.import_create_events
