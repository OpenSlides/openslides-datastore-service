from tests.system.shared import GET_IDS_URL, WRITE_URL


def test_wrong_method_write(client):
    response = client.get(WRITE_URL)
    assert response.status_code == 405


def test_wrong_method_get_ids(client):
    response = client.get(GET_IDS_URL)
    assert response.status_code == 405


def test_404_on_unknown_url_1(client):
    response = client.get("/") #test
    assert response.status_code == 404
    response = client.post("/", data={})
    assert response.status_code == 404


def test_404_on_unknown_url_2(client):
    response = client.get("/some/url")
    assert response.status_code == 404
    response = client.post("/some/url", data={})
    assert response.status_code == 404
