import json

from datastore.shared.postgresql_backend import EVENT_TYPES
from datastore.shared.util import META_POSITION, strip_reserved_fields


def setup_data(connection, cursor, models, deleted=False):
    max_pos = max(m[META_POSITION] for _, m in models.items())
    cursor.execute(
        "insert into positions (user_id, migration_index) values "
        + ",".join(["(0, 1)"] * max_pos)
    )
    for weight, (fqid, model) in enumerate(models.items()):
        data = json.loads(json.dumps(model))
        strip_reserved_fields(data)
        cursor.execute(
            "insert into events (position, fqid, type, data, weight) values (%s, %s, %s, %s, %s)",
            [
                model[META_POSITION],
                fqid,
                EVENT_TYPES.CREATE,
                json.dumps(data),
                weight,
            ],
        )
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()
