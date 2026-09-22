import gzip
import io
import json
import sys
from pathlib import Path

# Insert parent directory so app can be imported directly
sys.path.insert(0, str(Path(__file__).parents[1]))
import app

TOKEN = {"Authorization": "Bearer test-token"}


def call(method, path, body=None, headers=None, query=""):
    result = {}
    encoded = json.dumps(body).encode() if body is not None else b""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(encoded)),
        "wsgi.input": io.BytesIO(encoded),
        "REMOTE_ADDR": "127.0.0.1",
    }
    for key, value in (headers or {}).items():
        environ["HTTP_" + key.upper().replace("-", "_")] = value

    def start(status, response_headers):
        result.update(status=status, headers=dict(response_headers))

    raw = b"".join(app.application(environ, start))

    if result.get("headers", {}).get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)

    result["body"] = json.loads(raw) if raw else None
    return result


def payload(addr="Hostel A, Room 210"):
    return {
        "customerId": "stu-102",
        "items": [{"menuItemId": "menu-42", "quantity": 2}],
        "deliveryAddress": addr,
    }


def create(key="key-1", addr="Hostel A, Room 210"):
    return call("POST", "/orders", payload(addr), TOKEN | {"Idempotency-Key": key})


def setup_function():
    app.store.clear()
    app._rate_buckets.clear()


def test_create_returns_201_location_etag_and_security_headers():
    setup_function()
    res = create("k-init")
    assert res["status"].startswith("201")
    assert "Location" in res["headers"]
    assert res["headers"]["Location"] == "/orders/" + res["body"]["id"]
    assert "ETag" in res["headers"]
    assert res["headers"]["Cache-Control"] == "no-store"
    assert res["headers"]["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in res["headers"]
    assert res["headers"]["Access-Control-Allow-Origin"] == "*"


def test_idempotent_repeat_returns_original_order():
    setup_function()
    first = create("idem-test")
    repeated = create("idem-test")
    assert repeated["status"].startswith("201")
    assert repeated["body"]["id"] == first["body"]["id"]
    assert repeated["headers"]["Location"] == first["headers"]["Location"]
    assert repeated["headers"]["ETag"] == first["headers"]["ETag"]
    assert len(app.store.list()) == 1


def test_conditional_get_returns_304():
    setup_function()
    made = create("k-get")
    order_id = made["body"]["id"]
    etag = made["headers"]["ETag"]

    # If-None-Match matches -> 304 Not Modified
    res = call("GET", f"/orders/{order_id}", headers=TOKEN | {"If-None-Match": etag})
    assert res["status"].startswith("304")
    assert res["body"] is None
    assert res["headers"]["ETag"] == etag

    # If-None-Match does not match -> 200 OK
    res2 = call("GET", f"/orders/{order_id}", headers=TOKEN | {"If-None-Match": '"other-etag"'})
    assert res2["status"].startswith("200")
    assert res2["body"]["id"] == order_id


def test_conditional_patch_update_and_412():
    setup_function()
    made = create("k-patch")
    order_id = made["body"]["id"]
    current_etag = made["headers"]["ETag"]

    # Stale write -> 412 Precondition Failed
    res_stale = call(
        "PATCH",
        f"/orders/{order_id}",
        {"deliveryAddress": "New Room 303"},
        TOKEN | {"If-Match": '"stale-etag"'},
    )
    assert res_stale["status"].startswith("412")
    assert res_stale["body"]["status"] == 412

    # Fresh write -> 200 OK with new ETag
    res_ok = call(
        "PATCH",
        f"/orders/{order_id}",
        {"deliveryAddress": "New Room 303"},
        TOKEN | {"If-Match": current_etag},
    )
    assert res_ok["status"].startswith("200")
    assert res_ok["body"]["deliveryAddress"] == "New Room 303"
    assert res_ok["headers"]["ETag"] != current_etag


def test_conditional_delete_and_412():
    setup_function()
    made = create("k-del")
    order_id = made["body"]["id"]
    current_etag = made["headers"]["ETag"]

    # Stale delete -> 412 Precondition Failed
    res_stale = call("DELETE", f"/orders/{order_id}", headers=TOKEN | {"If-Match": '"stale"'})
    assert res_stale["status"].startswith("412")

    # Correct delete -> 204 No Content
    res_del = call("DELETE", f"/orders/{order_id}", headers=TOKEN | {"If-Match": current_etag})
    assert res_del["status"].startswith("204")
    assert res_del["body"] is None

    # Subsequent GET returns 404
    assert call("GET", f"/orders/{order_id}", headers=TOKEN)["status"].startswith("404")


def test_query_params_filtering_sorting_and_pagination():
    setup_function()
    create("k-p1", addr="Address 1")
    create("k-p2", addr="Address 2")
    create("k-p3", addr="Address 3")

    # List all
    res = call("GET", "/orders", headers=TOKEN, query="page=1&pageSize=2&sort=asc")
    assert res["status"].startswith("200")
    assert res["body"]["total"] == 3
    assert len(res["body"]["orders"]) == 2
    assert res["body"]["page"] == 1
    assert res["body"]["pageSize"] == 2

    # Filter by status
    res_filt = call("GET", "/orders", headers=TOKEN, query="status=CONFIRMED")
    assert res_filt["status"].startswith("200")
    assert res_filt["body"]["orders"] == []


def test_invalid_query_params_return_400():
    setup_function()
    assert call("GET", "/orders", headers=TOKEN, query="status=INVALID")["status"].startswith("400")
    assert call("GET", "/orders", headers=TOKEN, query="page=0")["status"].startswith("400")
    assert call("GET", "/orders", headers=TOKEN, query="pageSize=500")["status"].startswith("400")
    assert call("GET", "/orders", headers=TOKEN, query="sort=random")["status"].startswith("400")


def test_missing_token_returns_401_and_unknown_returns_404():
    setup_function()
    unauth = call("GET", "/orders")
    assert unauth["status"].startswith("401")
    assert "WWW-Authenticate" in unauth["headers"]

    not_found = call("GET", "/orders/nonexistent", headers=TOKEN)
    assert not_found["status"].startswith("404")


def test_malformed_body_uses_problem_shape():
    setup_function()
    res = call("POST", "/orders", {"customerId": "stu-1"}, TOKEN | {"Idempotency-Key": "bad-body"})
    assert res["status"].startswith("400")
    assert set(res["body"].keys()) == {"type", "title", "status", "detail"}


def test_content_negotiation_unsupported_accept_returns_406():
    setup_function()
    res = call("GET", "/orders", headers=TOKEN | {"Accept": "application/xml"})
    assert res["status"].startswith("406")
    assert res["body"]["status"] == 406


def test_options_discovery_and_cors():
    setup_function()
    # /orders OPTIONS
    res_orders = call("OPTIONS", "/orders")
    assert res_orders["status"].startswith("204")
    assert res_orders["headers"]["Allow"] == "GET, POST, OPTIONS"
    assert "Access-Control-Allow-Origin" in res_orders["headers"]

    # /orders/{id} OPTIONS
    res_item = call("OPTIONS", "/orders/ord-123")
    assert res_item["status"].startswith("204")
    assert res_item["headers"]["Allow"] == "GET, PATCH, DELETE, OPTIONS"


def test_method_override_patch_and_delete():
    setup_function()
    made = create("k-override")
    order_id = made["body"]["id"]
    etag = made["headers"]["ETag"]

    # POST with X-HTTP-Method-Override: PATCH
    res_patch = call(
        "POST",
        f"/orders/{order_id}",
        {"deliveryAddress": "Overridden Address"},
        TOKEN | {"X-HTTP-Method-Override": "PATCH", "If-Match": etag},
    )
    assert res_patch["status"].startswith("200")
    assert res_patch["body"]["deliveryAddress"] == "Overridden Address"


def test_cancellation_sub_resource():
    setup_function()
    made = create("k-cancel")
    order_id = made["body"]["id"]

    # First cancellation request -> 202 Accepted
    res_cancel = call(
        "POST",
        f"/orders/{order_id}/cancellation",
        {"reason": "Changed my mind"},
        headers=TOKEN,
    )
    assert res_cancel["status"].startswith("202")
    assert res_cancel["body"]["status"] == "CANCELLATION_REQUESTED"

    # Second cancellation request -> 409 Conflict
    res_dup = call(
        "POST",
        f"/orders/{order_id}/cancellation",
        {"reason": "Duplicate try"},
        headers=TOKEN,
    )
    assert res_dup["status"].startswith("409")


def test_rate_limiting_signal():
    setup_function()
    client_headers = {"Authorization": "Bearer rate-limited-client"}
    for _ in range(50):
        call("GET", "/orders", headers=client_headers)

    # 51st request exceeds budget
    res_blocked = call("GET", "/orders", headers=client_headers)
    assert res_blocked["status"].startswith("429")
    assert "Retry-After" in res_blocked["headers"]
    assert res_blocked["headers"]["X-RateLimit-Remaining"] == "0"


def test_gzip_compression_on_large_payload():
    setup_function()
    for i in range(5):
        create(f"k-gz-{i}", addr=f"Long address line description for testing gzip payload #{i}")

    # Request with Accept-Encoding: gzip
    res = call("GET", "/orders", headers=TOKEN | {"Accept-Encoding": "gzip"})
    assert res["status"].startswith("200")
    assert res["headers"].get("Content-Encoding") == "gzip"
    assert "orders" in res["body"]
