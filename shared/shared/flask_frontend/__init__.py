from .errors import (  # noqa
    ERROR_CODES,
    InvalidRequest,
    handle_internal_errors,
    register_error_handlers,
)


def unify_urls(*parts):
    return "/" + "/".join(p.strip("/") for p in parts)
