from datastore.shared.di import injector
from datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
    EnvironmentService,
)
from datastore.writer.core import Writer
from datastore.writer.services import register_services


def main():
    register_services()
    env_service: EnvironmentService = injector.get(EnvironmentService)
    writer: Writer = injector.get(Writer)

    env_service.set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "1")
    writer.truncate_db()


if __name__ == "__main__":
    main()
