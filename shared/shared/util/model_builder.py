from typing import Protocol

from shared.di import service_as_singleton, service_interface
from shared.postgresql_backend import ConnectionHandler


@service_interface
class ModelBuilder(Protocol):
    def build(self, fqid):
        ...


@service_as_singleton
class SqlModelBuilder:

    connection: ConnectionHandler

    def build(self, fqid):
        pass
