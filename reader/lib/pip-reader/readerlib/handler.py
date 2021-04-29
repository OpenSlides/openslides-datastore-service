from reader.flask_frontend.json_handler import JSONHandler
from reader.flask_frontend.routes import Route
from shared.flask_frontend import handle_internal_errors
from typing import Dict, Tuple


def handle_request(route: Route, data: Dict) -> Tuple[Dict, int]:
    handler = JSONHandler()
    # wrap function to catch thrown errors and return correct error dict
    handler_func = handle_internal_errors(handler.handle_request)
    result = handler_func(route, data)
    # add status code of 200 as default if no error occured
    if not isinstance(result, tuple):
        return result, 200
    else:
        return result
    