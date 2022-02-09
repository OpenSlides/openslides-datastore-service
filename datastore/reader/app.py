from datastore.reader.flask_frontend import FlaskFrontend
from datastore.reader.services import register_services
from datastore.shared import create_base_application

import datastore.shared.util.otel


def create_application():
    register_services()
    return create_base_application(FlaskFrontend)

application = create_application()

otel.init("datastore-reader")
#otel.instrument_flask(application)
