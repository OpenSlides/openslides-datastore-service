from textwrap import dedent
from typing import Any, Dict, List, Tuple

from shared.core import And, DeletedModelsBehaviour, Filter, FilterOperator, Not, Or
from shared.core.exceptions import ModelDoesNotExist
from shared.di import service_as_singleton
from shared.util import KEYSEPARATOR, BadCodingError

from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPES


@service_as_singleton
class SqlReadDatabaseBackendService:

    connection: ConnectionHandler

    def get_context(self):
        return self.connection.get_connection_context()

    def get(
        self,
        fqid: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.ALL_MODELS,
    ) -> Dict[str, Any]:
        models = self.get_many([fqid], get_deleted_models)
        try:
            return models[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def get_many(
        self,
        fqids: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.ALL_MODELS,
    ) -> Dict[str, Dict[str, Any]]:
        if not fqids:
            return {}

        arguments = [tuple(fqids)]
        del_cond = self.get_deleted_condition(get_deleted_models)
        query = f"""
            select fqid, data from models
            {"natural join models_lookup" if del_cond else ""}
            where fqid in %s {del_cond}"""
        result = self.connection.query(query, arguments)

        models = {model[0]: model[1] for model in result}
        return models

    def get_all(
        self,
        collection: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> List[Dict[str, Any]]:
        del_cond = self.get_deleted_condition(get_deleted_models)
        query = f"""
            select data from models
            {"natural join models_lookup" if del_cond else ""}
            where fqid like %s {del_cond}"""
        models = self.connection.query_list_of_single_values(
            query, [collection + KEYSEPARATOR + "%"]
        )
        return models

    def filter(self, collection: str, filter: Filter):
        query, arguments, fields = self.build_filter_query(collection, filter)
        models = self.connection.query_list_of_single_values(query, arguments, fields)
        return models

    def exists(self, collection: str, filter: Filter):
        models = self.filter(collection, filter)
        return len(models) > 0

    def build_filter_query(
        self, collection: str, filter: Filter, selected_field: str = "data"
    ):
        fields: List[str] = []
        arguments: List[str] = []
        filter_str = self.build_filter_str(filter, fields, arguments)
        query = f"select {{}} from models where fqid like %s and ({filter_str})"
        return (
            query,
            [collection + KEYSEPARATOR + "%"] + arguments,
            [selected_field] + fields,
        )

    def build_filter_str(self, filter: Filter, fields: List[str], arguments: List[str]):
        if isinstance(filter, Not):
            return (
                f"NOT ({self.build_filter_str(filter.not_filter, fields, arguments)})"
            )
        elif isinstance(filter, Or):
            return " OR ".join(
                f"({self.build_filter_str(part, fields, arguments)})"
                for part in filter.or_filter
            )
        elif isinstance(filter, And):
            return " AND ".join(
                f"({self.build_filter_str(part, fields, arguments)})"
                for part in filter.and_filter
            )
        elif isinstance(filter, FilterOperator):
            fields += [f"data->>'{filter.field}'"]
            arguments += [filter.value]
            return f"{{}} {filter.operator} %s"

    def get_deleted_condition(self, flag: DeletedModelsBehaviour) -> str:
        return (
            ""
            if flag == DeletedModelsBehaviour.ALL_MODELS
            else "and deleted = " + str(flag == DeletedModelsBehaviour.ONLY_DELETED)
        )

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

    def build_model_ignore_deleted(self, fqid: str) -> Dict[str, Any]:
        # building a model (and ignoring the latest delete/restore) is easy:
        # Get all events and skip any delete, restore or noop event. Then just
        # build the model: First the create, than a series of update events
        # and delete_fields events.
        # TODO: There might be a speedup: Get the model from the readdb first.
        # If the model exists there, read the position from it, use the model
        # as a starting point in `build_model_from_events` and just fetch all
        # events after the position.
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
            raise BadCodingError()

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
                raise BadCodingError()

        return model

    def json(self, data):
        return self.connection.to_json(data)
