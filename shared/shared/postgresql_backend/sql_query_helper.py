from typing import Dict, List, Set, Tuple

from shared.di import service_as_singleton
from shared.services.read_database import (
    AggregateFilterQueryFieldsParameters,
    BaseFilterQueryFieldsParameters,
    CountFilterQueryFieldsParameters,
    MappedFieldsFilterQueryFieldsParameters,
)
from shared.util import (
    KEYSEPARATOR,
    And,
    BadCodingError,
    DeletedModelsBehaviour,
    Filter,
    FilterOperator,
    Not,
    Or,
)


# extend if neccessary. first is always the default (should be int)
# min/max functions support the following:
# "any numeric, string, date/time, network, or enum type, or arrays of these types"
VALID_AGGREGATE_CAST_TARGETS = ["int"]

VALID_AGGREGATE_FUNCTIONS = ["min", "max", "count"]


@service_as_singleton
class SqlQueryHelper:
    def get_unique_mapped_fields(
        self, mapped_fields_per_fqid: Dict[str, List[str]]
    ) -> List[str]:
        if len(mapped_fields_per_fqid):
            unique_mapped_fields: Set[str] = set.union(
                *[set(fields) for fields in mapped_fields_per_fqid.values()]
            )
            return list(unique_mapped_fields)
        else:
            return []

    def mapped_fields_map_has_empty_entry(
        self, mapped_fields_per_fqid: Dict[str, List[str]]
    ) -> bool:
        return not len(mapped_fields_per_fqid) or any(
            len(fields) == 0 for fields in mapped_fields_per_fqid.values()
        )

    def get_deleted_condition(
        self, flag: DeletedModelsBehaviour, prepend_and: bool = True
    ) -> str:
        if flag == DeletedModelsBehaviour.ALL_MODELS:
            return ""

        return (
            ("and " if prepend_and else "")
            + "deleted = "
            + str(flag == DeletedModelsBehaviour.ONLY_DELETED)
        )

    def build_select_from_mapped_fields(
        self,
        unique_mapped_fields: List[str],
        mapped_fields_per_fqid: Dict[str, List[str]] = None,
    ) -> Tuple[str, List[str]]:
        if len(unique_mapped_fields) == 0 or (
            mapped_fields_per_fqid
            and self.mapped_fields_map_has_empty_entry(mapped_fields_per_fqid)
        ):
            # at least one collection needs all fields, so we just select data and
            # calculate the mapped_fields later
            return "data", []
        else:
            return (
                ", ".join(["data->%s AS {}"] * len(unique_mapped_fields)),
                unique_mapped_fields,
            )

    def build_filter_query(
        self,
        collection: str,
        filter: Filter,
        fields_params: BaseFilterQueryFieldsParameters = None,
        select_fqid: bool = False,
    ) -> Tuple[str, List[str], List[str]]:
        arguments: List[str] = []
        sql_parameters: List[str] = []
        filter_str = self.build_filter_str(filter, arguments)

        arguments = [collection + KEYSEPARATOR + "%"] + arguments

        if isinstance(fields_params, MappedFieldsFilterQueryFieldsParameters):
            fields, mapped_field_args = self.build_select_from_mapped_fields(
                fields_params.mapped_fields
            )
            arguments = mapped_field_args + arguments
            sql_parameters = fields_params.mapped_fields
        else:
            if isinstance(fields_params, CountFilterQueryFieldsParameters):
                fields = "count(*)"
            elif isinstance(fields_params, AggregateFilterQueryFieldsParameters):
                if fields_params.function not in VALID_AGGREGATE_FUNCTIONS:
                    raise BadCodingError(
                        "Invalid aggregate function: %s" % fields_params.function
                    )
                if fields_params.type not in VALID_AGGREGATE_CAST_TARGETS:
                    raise BadCodingError("Invalid cast type: %s" % fields_params.type)

                fields = f"{fields_params.function}((data->>%s)::{fields_params.type})"
                arguments = [fields_params.field] + arguments
            else:
                raise BadCodingError(
                    f"Invalid fields_params for build_filter_query: {fields_params}"
                )
            fields += f" AS {fields_params.function},\
                        (SELECT MAX(position) FROM positions) AS position"

        if select_fqid:
            fields = f"fqid as __fqid__, {fields}"

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
