from datastore.shared.postgresql_backend import setup_di as postgresql_setup_di
from datastore.shared.services import setup_di as util_setup_di
from datastore.writer import setup_di as writer_setup_di
from datastore.writer.redis_backend import setup_di as redis_setup_di


def register_services():
    util_setup_di()
    postgresql_setup_di()
    redis_setup_di()
    writer_setup_di()
