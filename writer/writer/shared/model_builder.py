from typing import Protocol

from writer.di import service_as_singleton, service_interface
from writer.postgresql_backend.connection_handler import ConnectionHandler


@service_interface
class ModelBuilder(Protocol):
    def build(self, fqid):
        ...


@service_as_singleton
class SqlModelBuilder:

    connection: ConnectionHandler

    def build(self, fqid):
        pass
