from textwrap import dedent
from typing import Any, Dict, List, Tuple

from writer.di import service_as_singleton

from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPES


@service_as_singleton
class SqlReadDatabaseBackendService:

    connection: ConnectionHandler

    def get_models(self, fqids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not fqids:
            return {}

        arguments = [tuple(fqids)]
        query = "select fqid, data from models where fqid in %s"
        result = self.connection.query(query, arguments)

        models = {model[0]: model[1] for model in result}
        return models

    def create_or_update_models(self, models: Dict[str, Dict[str, Any]]) -> None:
        if not models:
            return

        arguments: List[Any] = []
        value_placeholders = []
        for fqid, model in models.items():
            arguments.extend((fqid, self.json(model),))
            value_placeholders.append("(%s, %s)")
        values = ",".join(value_placeholders)

        statement = f"""
            insert into models (fqid, data) values {values}
            on conflict(fqid) do update set data=excluded.data;"""
        self.connection.execute(statement, arguments)

    def delete_models(self, fqids: List[str]) -> None:
        if not fqids:
            return

        arguments = [tuple(fqids)]
        query = "delete from models where fqid in %s"
        self.connection.execute(query, arguments)

    def build_deleted_model(self, fqid: str) -> Dict[str, Any]:
        # building a model (and ignoring the latest delete/restore) is easy:
        # Get all events and skip any delete, restore or noop event. Then just
        # build the model: First the create, then a series of update events
        # and delete_fields events.
        included_types = dedent(
            f"""\
            ('{EVENT_TYPES.CREATE}',
            '{EVENT_TYPES.UPDATE}',
            '{EVENT_TYPES.DELETE_FIELDS}')"""
        )
        query = (
            "select type, data from events where fqid=%s "
            + f"and type in {included_types} order by id asc"
        )

        events = self.connection.query(query, [fqid])
        return self.build_model_from_events(events)

    def build_model_from_events(
        self, events: List[Tuple[int, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        if not events:
            raise RuntimeError()

        create_event = events[0]
        assert create_event[0] == EVENT_TYPES.CREATE
        model = create_event[1]

        # apply all other update/delete_fields
        for event in events[1:]:
            if event[0] == EVENT_TYPES.UPDATE:
                model.update(event[1])
            elif event[0] == EVENT_TYPES.DELETE_FIELDS:
                for field in event[1]:
                    if field in model:
                        del model[field]
            else:
                raise RuntimeError()

        return model

    def json(self, data):
        return self.connection.to_json(data)
