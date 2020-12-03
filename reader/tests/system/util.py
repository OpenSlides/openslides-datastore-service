import json

from shared.postgresql_backend import EVENT_TYPES


def setup_data(connection, cursor, models, deleted=False):
    max_pos = max(m["meta_position"] for _, m in models.items())
    cursor.execute(
        "insert into positions (user_id) values " + ",".join(["(0)"] * max_pos)
    )
    for fqid, model in models.items():
        cursor.execute(
            "insert into events (position, fqid, type, data) values (%s, %s, %s, %s)",
            [model["meta_position"], fqid, EVENT_TYPES.CREATE, json.dumps(model)],
        )
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()
