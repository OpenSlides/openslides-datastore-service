from typing import Dict

import fastjsonschema
from dacite import Config, from_dict
from dacite.exceptions import MissingValueError

from reader.core import Reader
from shared.di import injector
from shared.flask_frontend import InvalidRequest, dev_only_route
from shared.typing import JSON
from shared.util import BadCodingError, logger

from .routes import Route, route_configurations


class JSONHandler:
    def handle_request(self, route: Route, data: JSON) -> Dict:
        """
        A generic handler for all requests. Parses the request to a python object
        according to the route_setup and execute the according route_handler.
        """

        try:
            route_configuration = route_configurations[route]
        except KeyError:
            raise BadCodingError("Invalid route metadata: " + route)

        logger.info(f"{route.upper()}-request: {data}")

        try:
            request_data = route_configuration.schema(data)
        except fastjsonschema.JsonSchemaException as e:
            if route_configuration.schema_error_handler:
                route_configuration.schema_error_handler(e)
            raise InvalidRequest(e.message)

        try:
            request_object = from_dict(
                route_configuration.request_class,
                request_data,
                Config(check_types=False),
            )
        except (TypeError, MissingValueError) as e:
            raise BadCodingError("Invalid data to initialize class\n" + str(e))

        reader = injector.get(Reader)
        route_handler = getattr(reader, route)

        if route_configuration.dev_only:
            route_handler = dev_only_route(route_handler)

        with reader.get_database_context():
            return route_handler(request_object)
