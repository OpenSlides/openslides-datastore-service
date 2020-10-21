from shared.flask_frontend import (
    JsonResponse,
    get_json_from_request,
    handle_internal_errors,
    unify_urls,
)

from .json_handler import JSONHandler
from .routes import Route


def get_route(route: Route):
    @handle_internal_errors
    def route_func():
        json_handler = JSONHandler()
        result = json_handler.handle_request(route, get_json_from_request())
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
