ALL_TABLES = (
    "positions",
    "events",
    "models_lookup",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "models",
)


def assert_error_response(response, type):
    assert response.status_code == 400
    assert isinstance(response.json.get("error"), dict)
    assert response.json["error"].get("type") == type
