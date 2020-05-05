import json
import sys
from typing import List
from urllib import request

from shared.di import injector
from shared.postgresql_backend import ConnectionHandler
from shared.util import build_fqid
from writer.app import register_services
from writer.core import BaseRequestEvent, RequestCreateEvent, Writer, WriteRequest


register_services()
connection: ConnectionHandler = injector.get(ConnectionHandler)
writer: Writer = injector.get(Writer)

with connection.get_connection_context():
    events_count = connection.query_single_value(
        "SELECT COUNT(*) FROM events LIMIT 1", []
    )
    if events_count:
        if len(sys.argv) > 1 and sys.argv[1] == "-f":
            print("Warning: database is not empty! Executing anyway...")
        else:
            print(
                "Error: Some events are already present, aborting.\
                If you wish to continue anyway, re-run with '-f'."
            )
            sys.exit(1)

raw = request.urlopen(
    "https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/example-data.json"  # noqa
).read()
data = json.loads(raw)

events: List[BaseRequestEvent] = []
for collection, models in data.items():
    for model in models:
        fqid = build_fqid(collection, model["id"])
        event = RequestCreateEvent(fqid, model)
        events.append(event)

write_request = WriteRequest(events, None, 0, {})
writer.write(write_request)
