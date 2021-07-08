from datastore.reader.core import setup_di as core_setup_di
from datastore.reader.flask_frontend import FlaskFrontend
from datastore.shared import create_base_application
from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di


def register_services():
    util_setup_di()
    postgresql_setup_di()
    core_setup_di()


def create_application():
    register_services()
    return create_base_application(FlaskFrontend)


application = create_application()
