from tests.system.util import GET_URL


def test_simple(json_client, db_cur):
    # db_cur.execute("insert into models values ('collection/1', '{\"data\": 1}')")
    response = json_client.post(GET_URL, {"fqid": "collection/1"})
    assert response.status_code == 200
