from flask import Flask

from .errors import register_error_handlers
from .routes import register_routes


URL_PREFIX = "/internal/datastore/writer/"


class FlaskFrontend:
    @classmethod
    def create_application(cls):
        app = Flask("datastore_writer")
        register_routes(app, URL_PREFIX)
        register_error_handlers(app)
        return app
