import json
from typing import Any, cast

from datastore.reader.core import GetEverythingRequest, Reader
from datastore.reader.services import register_services
from datastore.shared.di import injector
from datastore.shared.services import ReadDatabase
from datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
    EnvironmentService,
)
from datastore.shared.util import is_reserved_field


def main():
    register_services()
    env_service: EnvironmentService = injector.get(EnvironmentService)
    reader: Reader = injector.get(Reader)
    read_database: ReadDatabase = injector.get(ReadDatabase)

    env_service.set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "1")
    with reader.get_database_context():
        response = reader.get_everything(GetEverythingRequest())
        migration_index = read_database.get_current_migration_index()

    # strip meta fields
    for collection, models in response.items():
        for model in models.values():
            for field in list(model.keys()):
                if is_reserved_field(field):
                    del model[field]

    response["_migration_index"] = cast(Any, migration_index)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
