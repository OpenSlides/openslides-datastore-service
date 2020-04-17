from textwrap import dedent
from typing import Any, ContextManager, Dict, List, Optional, Set, Tuple, Union

from shared.core import (
    And,
    DeletedModelsBehaviour,
    Filter,
    FilterOperator,
    ModelDoesNotExist,
    Not,
    Or,
    collection_from_fqid,
)
from shared.di import service_as_singleton
from shared.util import KEYSEPARATOR, META_POSITION, BadCodingError, Model

from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPES


# extend if neccessary. first is always the default (should be int)
# min/max functions support the following:
# "any numeric, string, date/time, network, or enum type, or arrays of these types"
VALID_AGGREGATE_CAST_TARGETS = ["int"]


@service_as_singleton
class SqlReadDatabaseBackendService:

    VALID_AGGREGATE_FUNCTIONS = ["min", "max", "count"]

    connection: ConnectionHandler

    def get_context(self) -> ContextManager[None]:
        return self.connection.get_connection_context()

    def get(self, fqid: str, mapped_fields: List[str] = [],) -> Model:
        collection = collection_from_fqid(fqid)
        models = self.get_many([fqid], {collection: mapped_fields})
        try:
            return models[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def get_many(
        self,
        fqids: List[str],
        mapped_fields_per_collection: Dict[str, List[str]] = {},
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
        self,
        collection: str,
        filter: Filter,
        fields_params: Tuple[str, Optional[str], Optional[str]],
    ) -> Any:
        query, arguments, sql_params = self.build_filter_query(
            collection, filter, fields_params
        )
        value = self.connection.query(query, arguments, sql_params)
        return value[0].copy()

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
        if len(mapped_fields_per_collection):
            unique_mapped_fields: Set[str] = set.union(
                *[set(fields) for fields in mapped_fields_per_collection.values()]
            )
            return list(unique_mapped_fields)
        else:
            return []

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
        return not len(mapped_fields_per_collection) or any(
            len(fields) == 0 for fields in mapped_fields_per_collection.values()
        )

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

            if (
                collection in mapped_fields_per_collection
                and len(mapped_fields_per_collection[collection]) > 0
            ):
                for key in list(model.keys()):
                    if key not in mapped_fields_per_collection[collection]:
                        del model[key]
            result_map[fqid] = model

        return result_map

    def build_filter_query(
        self,
        collection: str,
        filter: Filter,
        fields_params: Union[
            List[str], Tuple[str, Optional[str], Optional[str]]
        ] = None,
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
            elif fields_params[0] not in self.VALID_AGGREGATE_FUNCTIONS:
                raise BadCodingError(f"Invalid aggregate function: {fields_params[0]}")
            else:
                if len(fields_params) == 3 and fields_params[1] and fields_params[2]:
                    if fields_params[2] not in VALID_AGGREGATE_CAST_TARGETS:
                        raise BadCodingError("Invalid cast type: %s" % fields_params[2])
                    fields = f"{fields_params[0]}((data->>%s)::{fields_params[2]})"
                    arguments = [fields_params[1]] + arguments  # type: ignore
                elif fields_params[0] == "count":
                    fields = "count(*)"
                else:
                    raise BadCodingError(
                        "Invalid fields_params for build_filter_query: %s"
                        % list(fields_params)
                    )
                fields += f" AS {fields_params[0]},\
                            (SELECT MAX(position) FROM positions) AS position"
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
            condition = f"data->>%s {filter.operator} %s::text"
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

    def create_or_update_models(self, models: Dict[str, Model]) -> None:
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

    def build_model_ignore_deleted(
        self, fqid: str, position: Optional[int] = None
    ) -> Model:
        models = self.build_models_ignore_deleted([fqid], position)
        try:
            return models[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def build_models_ignore_deleted(
        self, fqids: List[str], position: Optional[int] = None
    ) -> Dict[str, Model]:
        # building a model (and ignoring the latest delete/restore) is easy:
        # Get all events and skip any delete, restore or noop event. Then just
        # build the model: First the create, than a series of update events
        # and delete_fields events.
        # Optionally only builds the models up to the specified position.
        # TODO: There might be a speedup: Get the model from the readdb first.
        # If the model exists there, read the position from it, use the model
        # as a starting point in `build_model_from_events` and just fetch all
        # events after the position.
        if position:
            pos_cond = "and position <= %s"
            pos_args = [position]
        else:
            pos_cond = ""
            pos_args = []

        included_types = dedent(
            f"""\
            ('{EVENT_TYPES.CREATE}',
            '{EVENT_TYPES.UPDATE}',
            '{EVENT_TYPES.DELETE_FIELDS}')"""
        )
        query = dedent(
            f"""\
            select fqid, type, data, position from events e
            where fqid in %s and type in {included_types} {pos_cond}
            order by id asc"""
        )

        args: List[Any] = [tuple(fqids)]
        db_events = self.connection.query(query, args + pos_args)

        partitions = {}
        for event in db_events:
            if event["fqid"] not in partitions:
                partitions[event["fqid"]] = [event]
            else:
                partitions[event["fqid"]] += [event]

        models = {}
        for fqid, events in partitions.items():
            models[fqid] = self.build_model_from_events(events)

        return models

    def build_model_from_events(self, events: List[Dict[str, Any]]) -> Model:
        if not events:
            raise BadCodingError()

        create_event = events[0]
        assert create_event["type"] == EVENT_TYPES.CREATE
        model = create_event["data"]

        # apply all other update/delete_fields
        for event in events[1:]:
            if event["type"] == EVENT_TYPES.UPDATE:
                model.update(event["data"])
            elif event["type"] == EVENT_TYPES.DELETE_FIELDS:
                for field in event["data"]:
                    if field in model:
                        del model[field]
            else:
                raise BadCodingError()

        model[META_POSITION] = events[-1]["position"]
        return model

    def is_deleted(self, fqid: str, position: Optional[int] = None) -> bool:
        result = self.get_deleted_status([fqid], position)
        try:
            return result[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def get_deleted_status(
        self, fqids: List[str], position: Optional[int] = None
    ) -> Dict[str, bool]:
        if not position:
            return self.get_deleted_status_from_read_db(fqids)
        else:
            return self.get_deleted_status_from_events(fqids, position)

    def get_deleted_status_from_events(
        self, fqids: List[str], position: int
    ) -> Dict[str, bool]:
        included_types = dedent(
            f"""\
            ('{EVENT_TYPES.CREATE}',
            '{EVENT_TYPES.DELETE}',
            '{EVENT_TYPES.RESTORE}')"""
        )
        query = f"""
                select fqid, type from (
                    select fqid, max(position) as position from events
                    where type in {included_types} and position <= {position}
                    and fqid in %s group by fqid
                ) t natural join events
                """
        result = self.connection.query(query, [tuple(fqids)])
        return {row["fqid"]: row["type"] == EVENT_TYPES.DELETE for row in result}

    def get_deleted_status_from_read_db(self, fqids: List[str]) -> Dict[str, bool]:
        query = "select fqid, deleted from models_lookup where fqid in %s"
        result = self.connection.query(query, [tuple(fqids)])
        return {row["fqid"]: row["deleted"] for row in result}

    def json(self, data):
        return self.connection.to_json(data)
