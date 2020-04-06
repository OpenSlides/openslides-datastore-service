from textwrap import dedent
from typing import Any, Dict, List, Set, Tuple, Union

from shared.core import And, DeletedModelsBehaviour, Filter, FilterOperator, Not, Or
from shared.core.exceptions import ModelDoesNotExist
from shared.core.key_transforms import collection_from_fqid
from shared.di import service_as_singleton
from shared.util import KEYSEPARATOR, BadCodingError, Model

from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPES


@service_as_singleton
class SqlReadDatabaseBackendService:

    VALID_AGGREGATE_FUNCTIONS = ["min", "max", "count"]

    connection: ConnectionHandler

    def get_context(self) -> Any:
        return self.connection.get_connection_context()

    def get(
        self,
        fqid: str,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.ALL_MODELS,
    ) -> Model:
        collection = collection_from_fqid(fqid)
        models = self.get_many([fqid], {collection: mapped_fields}, get_deleted_models)
        try:
            return models[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def get_many(
        self,
        fqids: List[str],
        mapped_fields_per_collection: Dict[str, List[str]],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.ALL_MODELS,
    ) -> Dict[str, Model]:
        if not fqids:
            return {}

        arguments = [tuple(fqids)]
        del_cond = self.get_deleted_condition(get_deleted_models)
        unique_mapped_fields: List[Any] = self.get_unique_mapped_fields(
            mapped_fields_per_collection
        )
        mapped_fields_str = self.build_select_mapped_fields(unique_mapped_fields)

        query = f"""
            select fqid, {mapped_fields_str} from models
            {"natural join models_lookup" if del_cond else ""}
            where fqid in %s {del_cond}"""
        result = self.connection.query(
            query, unique_mapped_fields + arguments, unique_mapped_fields
        )

        models = self.build_models_from_result(result, mapped_fields_per_collection)
        return models

    def get_all(
        self,
        collection: str,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> List[Model]:
        del_cond = self.get_deleted_condition(get_deleted_models)
        mapped_fields_str = self.build_select_mapped_fields(mapped_fields)
        query = f"""
            select {mapped_fields_str} from models
            {"natural join models_lookup" if del_cond else ""}
            where fqid like %s {del_cond}"""
        models = self.fetch_list_of_models(
            query,
            mapped_fields + [collection + KEYSEPARATOR + "%"],
            mapped_fields,
            mapped_fields,
        )
        return models

    def filter(
        self, collection: str, filter: Filter, mapped_fields: List[str]
    ) -> List[Model]:
        query, arguments, sql_params = self.build_filter_query(
            collection, filter, mapped_fields
        )
        models = self.fetch_list_of_models(query, arguments, sql_params, mapped_fields)
        return models

    def aggregate(
        self, collection: str, filter: Filter, fields_params: Tuple[str, str]
    ) -> Any:
        query, arguments, sql_params = self.build_filter_query(
            collection, filter, fields_params
        )
        value = self.connection.query_single_value(query, arguments, sql_params)
        return value

    def fetch_list_of_models(
        self,
        query: str,
        arguments: List[str],
        sql_parameters: List[str],
        mapped_fields: List[str],
    ) -> List[Model]:
        result = self.connection.query(query, arguments, sql_parameters)
        if len(mapped_fields) > 0:
            models = [row.copy() for row in result]
        else:
            models = [row["data"] for row in result]
        return models

    def get_unique_mapped_fields(
        self, mapped_fields_per_collection: Dict[str, List[str]]
    ) -> List[str]:
        unique_mapped_fields: Set[str] = set.union(
            *[set(fields) for fields in mapped_fields_per_collection.values()]
        )
        return list(unique_mapped_fields)

    def build_select_mapped_fields(
        self,
        unique_mapped_fields: List[str],
        mapped_fields_per_collection: Dict[str, List[str]] = None,
    ) -> str:
        if len(unique_mapped_fields) == 0 or (
            mapped_fields_per_collection
            and self.mapped_fields_map_has_empty_entry(mapped_fields_per_collection)
        ):
            # at least one collection needs all fields, so we just select data and
            # calculate the mapped_fields later
            return "data"
        else:
            return ", ".join(["data->%s AS {}"] * len(unique_mapped_fields))

    def mapped_fields_map_has_empty_entry(
        self, mapped_fields_per_collection: Dict[str, List[str]]
    ) -> bool:
        return any(len(fields) == 0 for fields in mapped_fields_per_collection.values())

    def build_models_from_result(
        self, result, mapped_fields_per_collection: Dict[str, List[str]]
    ) -> Dict[str, Model]:
        result_map = {}
        for row in result:
            fqid = row["fqid"]
            collection = collection_from_fqid(fqid)

            if self.mapped_fields_map_has_empty_entry(mapped_fields_per_collection):
                # at least one collection needs all fields, so we just selected data
                model = row["data"]
            else:
                model = row.copy()

            if len(mapped_fields_per_collection[collection]) > 0:
                for key in list(model.keys()):
                    if key not in mapped_fields_per_collection[collection]:
                        del model[key]
            result_map[fqid] = model

        return result_map

    def build_filter_query(
        self,
        collection: str,
        filter: Filter,
        fields_params: Union[List[str], Tuple[str, str]] = None,
    ) -> Tuple[str, List[str], List[str]]:
        arguments: List[str] = []
        sql_parameters: List[str] = []
        filter_str = self.build_filter_str(filter, arguments)

        arguments = [collection + KEYSEPARATOR + "%"] + arguments

        if fields_params:
            if isinstance(fields_params, list):
                fields = self.build_select_mapped_fields(fields_params)
                arguments = fields_params + arguments
                sql_parameters = fields_params
            elif not fields_params[0] or not fields_params[1]:
                raise BadCodingError("You have to specify a function and a field")
            elif fields_params[0] not in self.VALID_AGGREGATE_FUNCTIONS:
                raise BadCodingError(f"Invalid aggregate function: {fields_params[0]}")
            else:
                fields = f"{fields_params[0]}(data->>%s)"
                arguments = [fields_params[1]] + arguments
        else:
            fields = "data"

        query = f"select {fields} from models where fqid like %s and ({filter_str})"
        return (
            query,
            arguments,
            sql_parameters,
        )

    def build_filter_str(self, filter: Filter, arguments: List[str]) -> str:
        if isinstance(filter, Not):
            return f"NOT ({self.build_filter_str(filter.not_filter, arguments)})"
        elif isinstance(filter, Or):
            return " OR ".join(
                f"({self.build_filter_str(part, arguments)})"
                for part in filter.or_filter
            )
        elif isinstance(filter, And):
            return " AND ".join(
                f"({self.build_filter_str(part, arguments)})"
                for part in filter.and_filter
            )
        elif isinstance(filter, FilterOperator):
            condition = f"data->>%s {filter.operator} %s"
            arguments += [filter.field, filter.value]
            return condition
        else:
            raise BadCodingError("Invalid filter type")

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
