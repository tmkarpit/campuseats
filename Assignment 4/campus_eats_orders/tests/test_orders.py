import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import app


def call(method, path, body=None, headers=None):
    result = {}
    encoded = json.dumps(body).encode() if body is not None else b""
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "", "CONTENT_LENGTH": str(len(encoded)), "wsgi.input": io.BytesIO(encoded)}
    for key, value in (headers or {}).items():
        environ["HTTP_" + key.upper().replace("-", "_")] = value
    def start(status, response_headers): result.update(status=status, headers=dict(response_headers))
    result["body"] = json.loads(b"".join(app.application(environ, start)))
    return result


def payload():
    return {"customerId": "stu-102", "items": [{"menuItemId": "menu-42", "quantity": 2}], "deliveryAddress": "Hostel A, Room 210"}


def setup_function(): app.store.clear()


def test_create_returns_201_and_location():
    response = call("POST", "/orders", payload(), {"Idempotency-Key": "key-1"})
    assert response["status"].startswith("201")
    assert response["headers"]["Location"] == "/orders/" + response["body"]["id"]


def test_idempotent_repeat_returns_original_order():
    first = call("POST", "/orders", payload(), {"Idempotency-Key": "key-1"})
    repeated = call("POST", "/orders", payload(), {"Idempotency-Key": "key-1"})
    assert repeated["status"].startswith("201")
    assert repeated["body"]["id"] == first["body"]["id"]
    assert len(app.store.list()) == 1


def test_malformed_body_uses_problem_shape():
    response = call("POST", "/orders", {"customerId": "stu-102"}, {"Idempotency-Key": "key-1"})
    assert response["status"].startswith("400")
    assert set(response["body"]) == {"type", "title", "status", "detail"}


def test_unknown_order_returns_404():
    response = call("GET", "/orders/not-real")
    assert response["status"].startswith("404")
