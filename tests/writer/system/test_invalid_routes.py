from datastore.writer.flask_frontend.routes import (
    RESERVE_IDS_URL,
    WRITE_ACTION_WORKER_URL,
    WRITE_URL,
)


def test_wrong_method_write(client):
    response = client.get(WRITE_URL)
    assert response.status_code == 405


def test_wrong_method_reserve_ids(client):
    response = client.get(RESERVE_IDS_URL)
    assert response.status_code == 405


def test_wrong_method_write_action_worker(client):
    response = client.get(WRITE_ACTION_WORKER_URL)
    assert response.status_code == 405


def test_404_on_unknown_url_1(client):
    response = client.get("/")
    assert response.status_code == 404
    response = client.post("/", data={})
    assert response.status_code == 404


def test_404_on_unknown_url_2(client):
    response = client.get("/some/url")
    assert response.status_code == 404
    response = client.post("/some/url", data={})
    assert response.status_code == 404
