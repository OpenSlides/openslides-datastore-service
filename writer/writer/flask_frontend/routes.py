from flask import request

from shared.core import (
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    ModelNotDeleted,
)
from shared.flask_frontend.errors import InvalidRequest

from .json_handlers import GetIdsHandler, WriteHandler


class ERROR_CODES:
    INVALID_FORMAT = 1
    INVALID_REQUEST = 2
    MODEL_DOES_NOT_EXIST = 3
    MODEL_EXISTS = 4
    MODEL_NOT_DELETED = 5
    MODEL_LOCKED = 6


def handle_errors(fn):
    def wrapper(*args, **kwargs):
        error_dict = None
        try:
            return fn(*args, **kwargs)
        except InvalidFormat as e:
            error_dict = {"type": ERROR_CODES.INVALID_FORMAT, "msg": e.msg}
        except InvalidRequest as e:
            error_dict = {"type": ERROR_CODES.INVALID_REQUEST, "msg": e.msg}
        except ModelDoesNotExist as e:
            error_dict = {"type": ERROR_CODES.MODEL_DOES_NOT_EXIST, "fqid": e.fqid}
        except ModelExists as e:
            error_dict = {"type": ERROR_CODES.MODEL_EXISTS, "fqid": e.fqid}
        except ModelNotDeleted as e:
            error_dict = {"type": ERROR_CODES.MODEL_NOT_DELETED, "fqid": e.fqid}
        except ModelLocked as e:
            error_dict = {"type": ERROR_CODES.MODEL_LOCKED, "key": e.key}
        return {"error": error_dict}, 400

    return wrapper


@handle_errors
def write():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    write_handler = WriteHandler()
    write_handler.write(request.get_json())
    return "", 200


@handle_errors
def get_ids():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    ids = GetIdsHandler().get_ids(request.get_json())
    return {"ids": ids}, 200


def unify_urls(*parts):
    return "/" + "/".join(p.strip("/") for p in parts)


def register_routes(app, url_prefix):
    write_url = unify_urls(url_prefix, "/write")
    app.add_url_rule(write_url, "write", write, methods=["POST"], strict_slashes=False)

    get_ids_url = unify_urls(url_prefix, "/get_ids")
    app.add_url_rule(
        get_ids_url, "get_ids", get_ids, methods=["POST"], strict_slashes=False
    )
