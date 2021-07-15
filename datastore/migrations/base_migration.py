from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from datastore.shared.typing import JSON

from .events import BaseEvent
from .exceptions import MigrationSetupException
from .migration_keyframes import MigrationKeyframeAccessor


@dataclass
class PositionData:
    position: int
    timestamp: datetime
    user_id: int
    information: JSON


class BaseMigration:
    target_migration_index = -1

    def __init__(self):
        self.name = self.__class__.__name__
        if self.target_migration_index == -1:
            raise MigrationSetupException(
                f"You need to specify target_migration_index of {self.name}"
            )

    def migrate(
        self,
        events: List[BaseEvent],
        old_accessor: MigrationKeyframeAccessor,
        new_accessor: MigrationKeyframeAccessor,
        position_data: PositionData,
    ) -> List[BaseEvent]:
        """
        Receives a list of events from one position to migrate. old_data and new_data
        provide access to the data of the datastore before this position, once
        unmigrated, once migrated. position_data contains auxillary data from the
        position to migrate.

        It should return a list of events which to fully replace all (provided)
        events of the position. If None is returned, this migration does not affect
        the position and the events of this position can be left as-is. It is ok to
        modify the provided events.
        """
        new_events: List[BaseEvent] = []
        for event in events:
            old_event = event.clone()
            translated_events = self.migrate_event(
                event, old_accessor, new_accessor, position_data
            )
            if translated_events is None:
                translated_events = [event]  # noop

            print("apply to old", old_event.fqid, old_event.get_data())
            old_accessor.apply_event(old_event)
            for translated_event in translated_events:
                print(
                    "apply to new", translated_event.fqid, translated_event.get_data()
                )
                new_accessor.apply_event(translated_event)

            new_events.extend(translated_events)

        return new_events

    def migrate_event(
        self,
        event: BaseEvent,
        old_accessor: MigrationKeyframeAccessor,
        new_accessor: MigrationKeyframeAccessor,
        position_data: PositionData,
    ) -> Optional[List[BaseEvent]]:
        """
        This needs to be implemented by each migration. This is the core logic of the
        migration to convert the given event. The provided event can be modified.
        """
        raise NotImplementedError()
