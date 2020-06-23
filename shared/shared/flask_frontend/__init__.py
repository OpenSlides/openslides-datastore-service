from .errors import (  # noqa
    ERROR_CODES,
    InvalidRequest,
    handle_internal_errors,
    register_error_handlers,
)
from .json_response import JsonResponse  # noqa


def unify_urls(*parts):
    return "/" + "/".join(p.strip("/") for p in parts)
