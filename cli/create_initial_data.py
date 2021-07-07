import json
import sys
from typing import List
from urllib import request
from urllib.error import URLError

from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import EnvironmentService
from datastore.shared.util import build_fqid
from datastore.writer.app import register_services
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    Writer,
    WriteRequest,
)


register_services()
connection: ConnectionHandler = injector.get(ConnectionHandler)
env_service: EnvironmentService = injector.get(EnvironmentService)
writer: Writer = injector.get(Writer)

with connection.get_connection_context():
    events_count = connection.query_single_value(
        "SELECT COUNT(*) FROM events LIMIT 1", []
    )
    if events_count:
        if len(sys.argv) > 1 and sys.argv[1] == "-f":
            print("Warning: database is not empty! Executing anyway...")
        else:
            print("Error: Some events are already present, aborting.")
            sys.exit(1)

path = env_service.get("DATASTORE_INITIAL_DATA_FILE")
print(f"Loading data: {path}")
if path.startswith("initial-data:"):
    data = json.loads(path.replace("initial-data:", "", 1))
else:
    if path.startswith("http://") or path.startswith("https://"):
        try:
            file = request.urlopen(path, timeout=20)
        except URLError:
            print(f"Timeout while fetching {path}")
            sys.exit(1)
    else:
        file = open(path)
    data = json.loads(file.read())

print("Create events")

events: List[BaseRequestEvent] = []
for collection, models in data.items():
    for model in models:
        fqid = build_fqid(collection, model["id"])
        event = RequestCreateEvent(fqid, model)
        events.append(event)

write_request = WriteRequest(events, None, 0, {})

print("Write events")
writer.write([write_request], log_all_modified_fields=False)

print(f"Wrote {len(events)} events to the datastore.")
