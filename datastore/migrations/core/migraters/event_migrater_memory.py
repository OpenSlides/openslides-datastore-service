import copy
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, cast

from datastore.shared.di import service_as_factory
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase
from datastore.shared.typing import Position

from ..events import BaseEvent
from ..migration_keyframes import InitialMigrationKeyframeModifier
from ..migration_logger import MigrationLogger
from .event_migrater import RawPosition
from .memory_migrater import MemoryMigrater
from .migrater import EventMigrater


@service_as_factory
class EventMigraterImplementationMemory(EventMigrater, MemoryMigrater):
    """
    This migrater is made for in memory migrations of meeting imports.
    The whole import will be imported to 1 position. Unlike the database
    migration, there is no need to have keyframes/baselines for all
    migrationlevels for the last position.
    """

    read_database: ReadDatabase
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        self.check_migration_index()
        position = RawPosition(
            position=1,
            migration_index=self.start_migration_index,
            timestamp=datetime.now(),
            user_id=0,
            information=None,
        )
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
        old_accessor, new_accessor = self.get_accessors(
            last_position_value,
            migration_index,
            migration_index + 1,
            position.position,
            False,
        )
        # TODO: Generate events from import data
        events = cast(List[BaseEvent], self.import_create_events)

        for (
            source_migration_index,
            target_migration_index,
            migration,
        ) in self.get_migrations(migration_index):
            self._reuse_accessor(old_accessor, source_migration_index)
            self._reuse_accessor(new_accessor, target_migration_index)

            events = migration.migrate(
                events, old_accessor, new_accessor, position.to_position_data()
            )

        self.migrated_events = events

    def get_accessors(
        self,
        last_position_value: Position,
        source_migration_index: int,
        target_migration_index: int,
        position: Position,
        _: bool,
    ) -> Tuple[InitialMigrationKeyframeModifier, InitialMigrationKeyframeModifier]:
        old_accessor = self._get_accessor(
            last_position_value,
            source_migration_index,
            position,
        )
        new_accessor = self._get_accessor(
            last_position_value,
            target_migration_index,
            position,
        )
        return old_accessor, new_accessor

    def _get_accessor(
        self, last_position_value: Position, migration_index, position: Position
    ) -> InitialMigrationKeyframeModifier:
        accessor = InitialMigrationKeyframeModifier(
            self.connection,
            last_position_value,
            migration_index,
            position,
        )
        return accessor

    def _reuse_accessor(
        self, accessor: InitialMigrationKeyframeModifier, migration_index
    ) -> None:
        accessor.migration_index = migration_index
        accessor.models = copy.deepcopy(self.imported_models)
        accessor.deleted = {key: False for key in self.imported_models}
        accessor.collection_ids = defaultdict(set)
