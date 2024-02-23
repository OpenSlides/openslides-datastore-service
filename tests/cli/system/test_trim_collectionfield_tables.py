from datetime import datetime, timedelta

from cli.trim_collectionfield_tables import main as trim_collectionfield_tables
from datastore.shared.di import injector


def test_trim_collectionfield_tables(db_cur):
    in_time = datetime.now() - timedelta(hours=12)
    out_time = datetime.now() - timedelta(hours=36)
    db_cur.execute(
        "INSERT INTO positions (timestamp, user_id, migration_index) VALUES (%s, -1, -1), (%s, -1, -1)",
        [out_time, in_time],
    )
    db_cur.execute(
        "INSERT INTO events (position, fqid, type, weight) VALUES (1, 'a/1', 'create', 1), (2, 'a/2', 'create', 1)",
        [],
    )
    db_cur.execute(
        "INSERT INTO collectionfields (collectionfield, position) VALUES ('a/f', 1), ('a/g', 2)",
        [],
    )
    db_cur.execute(
        "INSERT INTO events_to_collectionfields VALUES (1, 1), (1, 2), (2, 2)", []
    )
    db_cur.connection.commit()
    injector.provider_map.clear()  # de-register services for testing purposes
    trim_collectionfield_tables()
    db_cur.execute("SELECT * FROM collectionfields")
    assert db_cur.fetchall() == [(2, "a/g", 2)]
    db_cur.execute("SELECT * FROM events_to_collectionfields")
    assert db_cur.fetchall() == [(2, 2)]
