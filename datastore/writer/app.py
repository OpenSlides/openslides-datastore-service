import datastore.shared.util.otel as otel
from datastore.shared import create_base_application
from datastore.writer.flask_frontend import FlaskFrontend
from datastore.writer.services import register_services


def create_application():
    register_services()
    return create_base_application(FlaskFrontend)


application = create_application()

otel.init("datastore-writer")
otel.instrument_flask(application)
otel.instrument_redis()
