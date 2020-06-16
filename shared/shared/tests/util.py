def assert_response_code(response, code):
    assert response.status_code == code


def assert_error_response(response, type):
    assert_response_code(response, 400)
    json = response.json() if callable(response.json) else response.json
    assert isinstance(json.get("error"), dict)
    error_type = json["error"].get("type")
    assert error_type == type


def assert_success_response(response):
    assert_response_code(response, 200)
