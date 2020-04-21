ALL_TABLES = (
    "positions",
    "events",
    "models_lookup",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "models",
)


def assert_response_code(response, code):
    if response.status_code != code:
        print(response.json)
    assert response.status_code == code


def assert_error_response(response, type):
    assert_response_code(response, 400)
    assert isinstance(response.json.get("error"), dict)
    if (error_type := response.json["error"].get("type")) != type:
        print("Error type:", error_type)
    assert error_type == type


def assert_success_response(response):
    assert_response_code(response, 200)
