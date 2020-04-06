import json

from shared.tests.util import assert_success_response
from tests.system.util import MIN_URL


data = {
    "c1/1": {"field_1": "d", "meta_position": 2},
    "c1/2": {"field_1": "c", "meta_position": 3},
    "c1/3": {"field_1": "b", "meta_position": 4},
    "c2/1": {"field_1": "a", "meta_position": 1},
}


def setup_data(connection, cursor, deleted=False):
    for fqid, model in data.items():
        cursor.execute("insert into models values (%s, %s)", [fqid, json.dumps(model)])
        cursor.execute("insert into models_lookup values (%s, %s)", [fqid, deleted])
    connection.commit()


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur)
    response = json_client.post(
        MIN_URL,
        {
            "collection": "c1",
            "filter": {"field": "field_1", "operator": "!=", "value": "invalid"},
            "field": "meta_position",
        },
    )
    assert_success_response(response)
    assert response.json["min"] == "2"
