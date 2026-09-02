"""A dependency-free WSGI implementation of the CampusEats Orders service."""
import json
import os
import random
import time
from urllib import error, request

from errors import problem
from models import Order
from store import OrderStore

store = OrderStore()


def validate(body):
    """Hand-written equivalent of the XML Schema validation used in Assignment 3."""
    if not isinstance(body, dict):
        raise ValueError("Request body must be a JSON object.")
    required = ("customerId", "items", "deliveryAddress")
    missing = [field for field in required if field not in body]
    if missing:
        raise ValueError("Missing required field(s): " + ", ".join(missing) + ".")
    if not isinstance(body["customerId"], str) or not body["customerId"].strip():
        raise ValueError("customerId must be a non-empty string.")
    if not isinstance(body["deliveryAddress"], str) or not body["deliveryAddress"].strip():
        raise ValueError("deliveryAddress must be a non-empty string.")
    if not isinstance(body["items"], list) or not body["items"]:
        raise ValueError("items must be a non-empty array.")
    for item in body["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("menuItemId"), str):
            raise ValueError("Every item must contain a string menuItemId.")
        if not isinstance(item.get("quantity"), int) or item["quantity"] < 1:
            raise ValueError("Every item quantity must be an integer of at least 1.")


def charge_payment(order):
    """Safely retry only transient payment calls; 4xx responses are never retried."""
    base_url = os.environ.get("PAYMENTS_URL")
    if not base_url:
        return None  # documented fallback: retain a PAYMENT_PENDING order
    payload = json.dumps({"orderId": order.order_id, "amount": len(order.items) * 100}).encode()
    headers = {"Content-Type": "application/json", "Idempotency-Key": order.idempotency_key}
    for attempt in range(3):
        try:
            req = request.Request(base_url.rstrip("/") + "/payments", payload, headers, method="POST")
            with request.urlopen(req, timeout=2.0) as response:
                if 200 <= response.status < 300:
                    data = json.loads(response.read() or b"{}")
                    return data.get("id", "payment-accepted")
                return None
        except error.HTTPError as exc:
            if 400 <= exc.code < 500:
                return None
        except (error.URLError, TimeoutError, OSError):
            pass
        if attempt < 2:
            time.sleep((0.15 * (2**attempt)) + random.uniform(0, 0.10))
    return None


def _json_response(start_response, status, payload, extra_headers=None):
    data = json.dumps(payload).encode("utf-8")
    headers = [("Content-Type", "application/json"), ("Content-Length", str(len(data)))]
    headers.extend((extra_headers or {}).items())
    start_response(f"{status} {_reason(status)}", headers)
    return [data]


def _reason(status):
    return {200: "OK", 201: "Created", 202: "Accepted", 400: "Bad Request", 404: "Not Found", 409: "Conflict", 422: "Unprocessable Content", 503: "Service Unavailable"}[status]


def application(environ, start_response):
    method, path = environ["REQUEST_METHOD"], environ.get("PATH_INFO", "")
    try:
        if method == "POST" and path == "/orders":
            key = environ.get("HTTP_IDEMPOTENCY_KEY")
            if not key:
                status, headers, data = problem(400, "Missing Idempotency-Key", "An Idempotency-Key header is required.")
                start_response("400 Bad Request", list(headers.items())); return [data]
            try:
                length = int(environ.get("CONTENT_LENGTH") or 0)
                body = json.loads(environ["wsgi.input"].read(length) or b"null")
                validate(body)
            except (ValueError, json.JSONDecodeError) as exc:
                status, headers, data = problem(400, "Malformed order", str(exc))
                start_response("400 Bad Request", list(headers.items())); return [data]
            order, created = store.create_once(Order(body["customerId"], body["items"], body["deliveryAddress"], key))
            if created:
                payment_id = charge_payment(order)
                if payment_id:
                    order.payment_reference, order.status = payment_id, "CONFIRMED"
            return _json_response(start_response, 201, order.as_json(), {"Location": "/orders/" + order.order_id})

        if method == "GET" and path == "/orders":
            from urllib.parse import parse_qs
            status = parse_qs(environ.get("QUERY_STRING", "")).get("status", [None])[0]
            allowed = {None, "PAYMENT_PENDING", "CONFIRMED", "CANCELLATION_REQUESTED", "CANCELLED"}
            if status not in allowed:
                code, headers, data = problem(400, "Invalid status filter", "status is not a known order status.")
                start_response("400 Bad Request", list(headers.items())); return [data]
            return _json_response(start_response, 200, {"orders": [o.as_json() for o in store.list(status)]})

        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "orders":
            order = store.get(parts[1])
            if not order:
                code, headers, data = problem(404, "Order not found", "No order exists with that id.")
                start_response("404 Not Found", list(headers.items())); return [data]
            if method == "GET" and len(parts) == 2:
                return _json_response(start_response, 200, order.as_json())
            if method == "POST" and len(parts) == 3 and parts[2] == "cancellation":
                try:
                    length = int(environ.get("CONTENT_LENGTH") or 0)
                    cancellation = json.loads(environ["wsgi.input"].read(length) or b"{}")
                    if not isinstance(cancellation, dict) or ("reason" in cancellation and not isinstance(cancellation["reason"], str)):
                        raise ValueError("Cancellation body must be an object with an optional string reason.")
                except (ValueError, json.JSONDecodeError) as exc:
                    code, headers, data = problem(400, "Malformed cancellation", str(exc))
                    start_response("400 Bad Request", list(headers.items())); return [data]
                if order.status in {"CANCELLATION_REQUESTED", "CANCELLED"}:
                    code, headers, data = problem(409, "Cancellation already requested", "The order is already being cancelled.")
                    start_response("409 Conflict", list(headers.items())); return [data]
                if order.status not in {"PAYMENT_PENDING", "CONFIRMED"}:
                    code, headers, data = problem(422, "Order cannot be cancelled", "Only pending or confirmed orders may be cancelled.")
                    start_response("422 Unprocessable Content", list(headers.items())); return [data]
                order.status = "CANCELLATION_REQUESTED"
                return _json_response(start_response, 202, order.as_json())
        code, headers, data = problem(404, "Not found", "No endpoint matches this URL.")
        start_response("404 Not Found", list(headers.items())); return [data]
    except Exception:
        code, headers, data = problem(503, "Service unavailable", "The service could not complete the request safely.")
        start_response("503 Service Unavailable", list(headers.items())); return [data]


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("Orders service listening on http://127.0.0.1:8001")
    make_server("127.0.0.1", 8001, application).serve_forever()
