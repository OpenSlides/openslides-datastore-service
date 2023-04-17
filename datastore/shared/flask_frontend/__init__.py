from flask import request
from werkzeug.exceptions import BadRequest

from .dev_only_route import dev_only_route
from .errors import (
    ERROR_CODES,
    InvalidRequest,
    handle_internal_errors,
    register_error_handlers,
)
from .json_response import JsonResponse


def unify_urls(*parts):
    return "/" + "/".join(p.strip("/") for p in parts)


def get_json_from_request():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    try:
        return request.get_json()
    except BadRequest:
        # Will be fired on empty payload, but we will treat empty as None
        return None
