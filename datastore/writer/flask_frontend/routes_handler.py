from typing import Any, Dict, List, cast

from flask import request

from datastore.shared.di import injector
from datastore.shared.flask_frontend import (
    InvalidRequest,
    JsonResponse,
    dev_only_route,
    handle_internal_errors,
)
from datastore.shared.util.key_transforms import collection_from_fqid
from datastore.writer.core import Writer
from datastore.writer.flask_frontend.routes import (  # noqa
    DELETE_HISTORY_INFORMATION_URL,
    RESERVE_IDS_URL,
    TRUNCATE_DB_URL,
    WRITE_ACTION_WORKER_URL,
    WRITE_URL,
)

from .json_handlers import ReserveIdsHandler, WriteHandler


@handle_internal_errors
def write():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    write_handler = WriteHandler()
    write_handler.write(request.get_json())
    return "", 201


@handle_internal_errors
def reserve_ids():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    reserve_ids_handler = ReserveIdsHandler()
    ids = reserve_ids_handler.reserve_ids(request.get_json())
    return JsonResponse({"ids": ids})


@handle_internal_errors
def write_action_worker():
    if not request.is_json:
        raise InvalidRequest("Data must be json")
    if type(request.json) != list:
        raise InvalidRequest("write_action_worker data internally must be a list!")
    req_json = cast(List[Dict[str, Any]], request.json)[0]
    if len(req_json.get("events", ())) != 1 and any(
        event["type"] != "delete" for event in req_json.get("events", ())
    ):
        raise InvalidRequest("write_action_worker may contain only 1 event!")
    if any(
        collection_from_fqid(event["fqid"]) != "action_worker"
        for event in req_json.get("events", ())
    ):
        raise InvalidRequest("Collection for write_action_worker must be action_worker")
    write_handler = WriteHandler()
    write_handler.write_action_worker(req_json)
    return_code = 200 if req_json.get("events", ())[0]["type"] == "delete" else 201
    return ("", return_code)


@dev_only_route
@handle_internal_errors
def truncate_db():
    writer = injector.get(Writer)
    writer.truncate_db()
    return "", 204


@handle_internal_errors
def delete_history_information():
    writer = injector.get(Writer)
    writer.delete_history_information()
    return "", 204


def register_routes(app, url_prefix):
    for route in (
        "write",
        "reserve_ids",
        "delete_history_information",
        "truncate_db",
        "write_action_worker",
    ):
        app.add_url_rule(
            globals()[f"{route.upper()}_URL"],
            route,
            globals()[route],
            methods=["POST"],
            strict_slashes=False,
        )
