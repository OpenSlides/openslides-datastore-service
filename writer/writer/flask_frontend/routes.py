from flask import request

from shared.flask_frontend import InvalidRequest, handle_internal_errors, unify_urls

from .json_handlers import ReserveIdsHandler, WriteHandler


@handle_internal_errors
def write():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    write_handler = WriteHandler()
    write_handler.write(request.get_json())
    return "", 200


@handle_internal_errors
def reserve_ids():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    ids = ReserveIdsHandler().reserve_ids(request.get_json())
    return {"ids": ids}, 200


def register_routes(app, url_prefix):
    write_url = unify_urls(url_prefix, "/write")
    app.add_url_rule(write_url, "write", write, methods=["POST"], strict_slashes=False)

    reserve_ids_url = unify_urls(url_prefix, "/reserve_ids")
    app.add_url_rule(
        reserve_ids_url,
        "reserve_ids",
        reserve_ids,
        methods=["POST"],
        strict_slashes=False,
    )
