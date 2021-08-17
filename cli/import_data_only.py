import json
import sys
from typing import List

from datastore.shared.di import injector
from datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
    EnvironmentService,
)
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    Writer,
    WriteRequest,
)
from datastore.writer.services import register_services


def main():
    stdin_data = sys.stdin.read()
    data = json.loads(stdin_data)

    register_services()
    env_service: EnvironmentService = injector.get(EnvironmentService)
    writer: Writer = injector.get(Writer)

    env_service.set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "1")
    writer.truncate_db()

    events: List[BaseRequestEvent] = []
    migration_index = -1
    for collection, models in data.items():
        if collection == "_migration_index":
            migration_index = models
            continue

        for id, model in models.items():
            fqid = fqid_from_collection_and_id(collection, id)
            event = RequestCreateEvent(fqid, model)
            events.append(event)

    write_request = WriteRequest(events, None, 0, {}, migration_index)
    writer.write([write_request], log_all_modified_fields=False)


if __name__ == "__main__":
    main()
