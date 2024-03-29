from datastore.reader import setup_di as reader_setup_di
from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di


def register_services():
    util_setup_di()
    postgresql_setup_di()
    reader_setup_di()
