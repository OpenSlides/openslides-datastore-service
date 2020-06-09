from shared.di import injector
from shared.postgresql_backend import ConnectionHandler
from shared.util import ALL_TABLES
from writer.app import register_services


register_services()
connection: ConnectionHandler = injector.get(ConnectionHandler)

with connection.get_connection_context():
    for table in ALL_TABLES:
        connection.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE", [])
