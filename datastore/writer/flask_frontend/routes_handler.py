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
from datastore.writer.flask_frontend.routes import (
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
    if len(request.json) != 1 or len(request.json[0]["events"]) != 1:  # type: ignore
        raise InvalidRequest("write_action_worker may contain only 1 event!")
    if collection_from_fqid(request.json[0]["events"][0]["fqid"]) != "action_worker":  # type: ignore
        raise InvalidRequest("Collection for write_action_worker must be action_worker")
    write_handler = WriteHandler()
    write_handler.write(request.json)
    return "", 201 if request.json[0]["events"][0]["type"] == "create" else 200  # type: ignore


@dev_only_route
@handle_internal_errors
def truncate_db():
    writer = injector.get(Writer)
    writer.truncate_db()
    return "", 204


def register_routes(app, url_prefix):
    app.add_url_rule(WRITE_URL, "write", write, methods=["POST"], strict_slashes=False)

    app.add_url_rule(
        RESERVE_IDS_URL,
        "reserve_ids",
        reserve_ids,
        methods=["POST"],
        strict_slashes=False,
    )

    app.add_url_rule(
        TRUNCATE_DB_URL,
        "truncate_db",
        truncate_db,
        methods=["POST"],
        strict_slashes=False,
    )

    app.add_url_rule(
        WRITE_ACTION_WORKER_URL,
        "write_action_worker",
        write_action_worker,
        methods=["POST"],
        strict_slashes=False,
    )
