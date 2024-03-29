from flask import Flask

from datastore.shared.flask_frontend import register_error_handlers

from .routes import URL_PREFIX
from .routes_handler import register_routes


class FlaskFrontend:
    @classmethod
    def create_application(cls):
        app = Flask("datastore_reader")
        register_routes(app, URL_PREFIX)
        register_error_handlers(app)
        return app
