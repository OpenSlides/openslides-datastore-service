from flask import request

from shared.flask_frontend import (
    InvalidRequest,
    JsonResponse,
    handle_internal_errors,
    unify_urls,
)

from .json_handler import JSONHandler
from .routes import Route


def get_route(route: Route):
    @handle_internal_errors
    def route_func():
        if not request.is_json:
            raise InvalidRequest("Data must be json")

        json_handler = JSONHandler()
        result = json_handler.handle_request(route, request.get_json())
        return JsonResponse(result)

    return route_func


def register_routes(app, url_prefix):
    for route in list(Route):
        url = unify_urls(url_prefix, route)
        app.add_url_rule(
            url,
            route,
            get_route(route),
            methods=["POST"],
            strict_slashes=False,
        )
