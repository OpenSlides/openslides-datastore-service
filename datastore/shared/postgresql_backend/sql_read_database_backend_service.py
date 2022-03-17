from collections import defaultdict
from textwrap import dedent
from typing import Any, ContextManager, Dict, Iterable, List, Optional

from datastore.shared.di import service_as_singleton
from datastore.shared.postgresql_backend import apply_fields
from datastore.shared.postgresql_backend.sql_query_helper import SqlQueryHelper
from datastore.shared.services.read_database import (
    BaseAggregateFilterQueryFieldsParameters,
    HistoryInformation,
    MappedFieldsFilterQueryFieldsParameters,
)
from datastore.shared.typing import Collection, Field, Fqid, Id, Model, Position
from datastore.shared.util import (
    META_DELETED,
    META_POSITION,
    BadCodingError,
    DeletedModelsBehaviour,
    Filter,
    InvalidDatastoreState,
    ModelDoesNotExist,
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
    get_exception_for_deleted_models_behaviour,
    id_from_fqid,
)

from .connection_handler import ConnectionHandler
from .sql_event_types import EVENT_TYPE


MIGRATION_INDEX_NOT_INITIALIZED = -2


@service_as_singleton
class SqlReadDatabaseBackendService:

    connection: ConnectionHandler
    query_helper: SqlQueryHelper

    current_migration_index: int = MIGRATION_INDEX_NOT_INITIALIZED

    def get_context(self) -> ContextManager[None]:
        return self.connection.get_connection_context()

    def get(
        self,
        fqid: Fqid,
        mapped_fields: List[Field] = [],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Model:
        models = self.get_many([fqid], {fqid: mapped_fields}, get_deleted_models)
        try:
            return models[fqid]
        except KeyError:
            raise get_exception_for_deleted_models_behaviour(fqid, get_deleted_models)

    def get_many(
        self,
        fqids: Iterable[Fqid],
        mapped_fields_per_fqid: Dict[Fqid, List[Field]] = {},
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Dict[Fqid, Model]:
        if not fqids:
            return {}

        arguments: List[Any] = [tuple(fqids)]
        del_cond = self.query_helper.get_deleted_condition(get_deleted_models)
        unique_mapped_fields = self.query_helper.get_unique_mapped_fields(
            mapped_fields_per_fqid
        )

        (
            mapped_fields_str,
            mapped_field_args,
        ) = self.query_helper.build_select_from_mapped_fields(
            unique_mapped_fields, mapped_fields_per_fqid
        )

        query = f"""
            select fqid, {mapped_fields_str} from models
            where fqid in %s {del_cond}"""
        result = self.connection.query(
            query, mapped_field_args + arguments, unique_mapped_fields
        )

        models = self.build_models_from_result(result, mapped_fields_per_fqid)
        return models

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[Field],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Dict[Id, Model]:
        del_cond = self.query_helper.get_deleted_condition(get_deleted_models)
        (
            mapped_fields_str,
            mapped_field_args,
        ) = self.query_helper.build_select_from_mapped_fields(mapped_fields)
        query = f"""
            select fqid as __fqid__, {mapped_fields_str} from models
            where fqid like %s {del_cond}"""
        models = self.fetch_models(
            query,
            mapped_field_args + [fqid_from_collection_and_id(collection, "%")],
            mapped_fields,
            mapped_fields,
        )
        return models

    def get_everything(
        self,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
    ) -> Dict[Collection, Dict[Id, Model]]:
        del_cond = self.query_helper.get_deleted_condition(
            get_deleted_models, prepend_and=False
        )
        query = f"""
            select fqid as __fqid__, data from models
            {"where " + del_cond if del_cond else ""}"""
        result = self.connection.query(query, [], [])

        data: Dict[Collection, Dict[Id, Model]] = defaultdict(dict)
        for row in result:
            collection, id = collection_and_id_from_fqid(row["__fqid__"])
            model = row["data"]
            model["id"] = id
            data[collection][id] = model

        return data

    def filter(
        self, collection: Collection, filter: Filter, mapped_fields: List[Field]
    ) -> Dict[Id, Model]:
        fields_params = MappedFieldsFilterQueryFieldsParameters(mapped_fields)
        query, arguments, sql_params = self.query_helper.build_filter_query(
            collection, filter, fields_params, select_fqid=True
        )
        models = self.fetch_models(query, arguments, sql_params, mapped_fields)
        return models

    def aggregate(
        self,
        collection: Collection,
        filter: Filter,
        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> Any:
        query, arguments, sql_params = self.query_helper.build_filter_query(
            collection, filter, fields_params
        )
        value = self.connection.query(query, arguments, sql_params)
        return value[0].copy()

    def fetch_models(
        self,
        query: str,
        arguments: List[str],
        sql_parameters: List[str],
        mapped_fields: List[str],
    ) -> Dict[int, Model]:
        """Fetched models for one collection"""
        result = self.connection.query(query, arguments, sql_parameters)
        models = {}
        for row in result:
            # if there are mapped_fields, we already resolved them in the query and
            # can just copy all fields. else we can just use the whole `data` field
            if len(mapped_fields) > 0:
                model = row.copy()
                del model["__fqid__"]
            else:
                model = row["data"]
            models[id_from_fqid(row["__fqid__"])] = model
        return models

    def build_models_from_result(
        self, result, mapped_fields_per_fqid: Dict[str, List[str]]
    ) -> Dict[str, Model]:
        result_map = {}
        has_empty_entries = self.query_helper.mapped_fields_map_has_empty_entry(
            mapped_fields_per_fqid
        )
        for row in result:
            fqid = row["fqid"]

            if has_empty_entries:
                # at least one collection needs all fields, so we need to select data
                row = row["data"]

            if fqid in mapped_fields_per_fqid and len(mapped_fields_per_fqid[fqid]) > 0:
                model = {}
                for field in mapped_fields_per_fqid[fqid]:
                    if row.get(field) is not None:
                        model[field] = row[field]
            else:
                model = row
            result_map[fqid] = model

        return result_map

    def build_model_ignore_deleted(
        self, fqid: Fqid, position: Optional[Position] = None
    ) -> Model:
        models = self.build_models_ignore_deleted([fqid], position)
        try:
            return models[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def build_models_ignore_deleted(
        self, fqids: List[Fqid], position: Optional[Position] = None
    ) -> Dict[Fqid, Model]:
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

        query = dedent(
            f"""\
            select fqid, type, data, position from events e
            where fqid in %s {pos_cond}
            order by position asc, weight asc"""
        )

        args: List[Any] = [tuple(fqids)]
        db_events = self.connection.query(query, args + pos_args)

        events_per_fqid: Dict[Fqid, List[Dict[str, Any]]] = defaultdict(list)
        for event in db_events:
            events_per_fqid[event["fqid"]].append(event)

        models = {}
        for fqid, events in events_per_fqid.items():
            models[fqid] = self.build_model_from_events(events)

        return models

    def build_model_from_events(self, events: List[Dict[str, Any]]) -> Model:
        if not events:
            raise BadCodingError()

        create_event = events[0]
        assert create_event["type"] == EVENT_TYPE.CREATE
        model: Model = {**create_event["data"], META_DELETED: False}

        # apply all other update/delete_fields
        for event in events[1:]:
            if event["type"] == EVENT_TYPE.UPDATE:
                model.update(event["data"])
            elif event["type"] == EVENT_TYPE.DELETE_FIELDS:
                for field in event["data"]:
                    if field in model:
                        del model[field]
            elif event["type"] == EVENT_TYPE.LIST_FIELDS:
                for field, value in apply_fields(
                    model, event["data"]["add"], event["data"]["remove"]
                ).items():
                    model[field] = value
            elif event["type"] == EVENT_TYPE.DELETE:
                model[META_DELETED] = True
            elif event["type"] == EVENT_TYPE.RESTORE:
                model[META_DELETED] = False
            else:
                raise BadCodingError()

        model[META_POSITION] = events[-1]["position"]
        return model

    def is_deleted(self, fqid: Fqid, position: Optional[Position] = None) -> bool:
        result = self.get_deleted_status([fqid], position)
        try:
            return result[fqid]
        except KeyError:
            raise ModelDoesNotExist(fqid)

    def get_deleted_status(
        self, fqids: List[Fqid], position: Optional[Position] = None
    ) -> Dict[Fqid, bool]:
        if not position:
            return self.get_deleted_status_from_read_db(fqids)
        else:
            return self.get_deleted_status_from_events(fqids, position)

    def get_deleted_status_from_read_db(self, fqids: List[Fqid]) -> Dict[Fqid, bool]:
        query = "select fqid, deleted from models where fqid in %s"
        result = self.connection.query(query, [tuple(fqids)])
        return {row["fqid"]: row["deleted"] for row in result}

    def get_deleted_status_from_events(
        self, fqids: List[Fqid], position: Position
    ) -> Dict[Fqid, bool]:
        included_types = dedent(
            f"""\
            ('{EVENT_TYPE.CREATE}',
            '{EVENT_TYPE.DELETE}',
            '{EVENT_TYPE.RESTORE}')"""
        )
        query = f"""
                select fqid, type from (
                    select fqid, max(position) as position from events
                    where type in {included_types} and position <= {position}
                    and fqid in %s group by fqid
                ) t natural join events order by position asc, weight asc
                """
        result = self.connection.query(query, [tuple(fqids)])
        return {row["fqid"]: row["type"] == EVENT_TYPE.DELETE for row in result}

    def get_history_information(
        self, fqids: List[Fqid]
    ) -> Dict[Fqid, List[HistoryInformation]]:
        positions = self.connection.query(
            """select fqid, position, timestamp, user_id, information from positions natural join events
            where fqid in %s and information::text<>%s::text order by position asc""",
            [tuple(fqids), self.json(None)],
        )
        history_information = defaultdict(list)
        for position in positions:
            history_information[position["fqid"]].append(
                HistoryInformation(
                    position=position["position"],
                    timestamp=position["timestamp"].timestamp(),
                    user_id=position["user_id"],
                    information=position["information"],
                )
            )
        return history_information

    def is_empty(self) -> bool:
        return not self.connection.query_single_value(
            "select exists(select * from positions)", []
        )

    def get_max_position(self) -> Position:
        return self.connection.query_single_value(
            "select max(position) from positions", []
        )

    def get_current_migration_index(self) -> int:
        if self.current_migration_index == MIGRATION_INDEX_NOT_INITIALIZED:
            [(min_migration_index, max_migration_index)] = self.connection.query(
                "select min(migration_index), max(migration_index) from positions", []
            )
            if min_migration_index != max_migration_index:
                raise InvalidDatastoreState(
                    "The datastore has inconsistent migration indices: "
                    + f"Minimum is {min_migration_index}, maximum is {max_migration_index}."
                )
            self.current_migration_index = max_migration_index or -1
        return self.current_migration_index

    def json(self, data):
        return self.connection.to_json(data)

    def reset(self) -> None:
        self.current_migration_index = MIGRATION_INDEX_NOT_INITIALIZED
