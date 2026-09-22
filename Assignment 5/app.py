"""CampusEats Orders: a dependency-free WSGI HTTP service implementing Assignment 5 HTTP methods and headers."""
import gzip
import hashlib
import json
import os
import random
import time
from collections import defaultdict
from urllib import error, request
from urllib.parse import parse_qs

from errors import problem
from models import Order
from store import OrderStore

store = OrderStore()
RATE_LIMIT, RATE_WINDOW_SECONDS = 50, 60
_rate_buckets = defaultdict(list)


def validate(body):
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


def validate_patch(body):
    if not isinstance(body, dict) or set(body) != {"deliveryAddress"}:
        raise ValueError("Patch body must contain only deliveryAddress.")
    if not isinstance(body["deliveryAddress"], str) or not body["deliveryAddress"].strip():
        raise ValueError("deliveryAddress must be a non-empty string.")


def charge_payment(order):
    """Timeout + safe retry of the optional Payments dependency."""
    base_url = os.environ.get("PAYMENTS_URL")
    if not base_url:
        return None
    payload = json.dumps({"orderId": order.order_id, "amount": len(order.items) * 100}).encode()
    headers = {"Content-Type": "application/json", "Idempotency-Key": order.idempotency_key}
    for attempt in range(3):
        try:
            req = request.Request(base_url.rstrip("/") + "/payments", payload, headers, method="POST")
            with request.urlopen(req, timeout=2.0) as response:
                if 200 <= response.status < 300:
                    return json.loads(response.read() or b"{}").get("id", "payment-accepted")
                return None
        except error.HTTPError as exc:
            if 400 <= exc.code < 500:
                return None
        except (error.URLError, TimeoutError, OSError):
            pass
        if attempt < 2:
            time.sleep((0.15 * (2 ** attempt)) + random.uniform(0, 0.10))
    return None


_REASONS = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    406: "Not Acceptable",
    409: "Conflict",
    412: "Precondition Failed",
    422: "Unprocessable Content",
    429: "Too Many Requests",
    503: "Service Unavailable",
}


def _rate_headers(environ):
    client = environ.get("HTTP_AUTHORIZATION") or environ.get("REMOTE_ADDR", "anonymous")
    now, bucket = time.time(), _rate_buckets[client]
    bucket[:] = [stamp for stamp in bucket if stamp > now - RATE_WINDOW_SECONDS]
    if len(bucket) >= RATE_LIMIT:
        retry_after = max(1, int(bucket[0] + RATE_WINDOW_SECONDS - now))
        return False, {
            "X-RateLimit-Limit": str(RATE_LIMIT),
            "X-RateLimit-Remaining": "0",
            "Retry-After": str(retry_after),
        }
    bucket.append(now)
    return True, {
        "X-RateLimit-Limit": str(RATE_LIMIT),
        "X-RateLimit-Remaining": str(RATE_LIMIT - len(bucket)),
    }


def _headers(environ, rate_headers, extra=None):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": environ.get("HTTP_ORIGIN", "*"),
        "Access-Control-Allow-Headers": (
            "Authorization, Content-Type, Idempotency-Key, If-None-Match, "
            "If-Match, X-HTTP-Method-Override, Accept, Accept-Encoding"
        ),
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Expose-Headers": "Location, ETag, X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After, Content-Encoding",
        "Vary": "Accept, Accept-Encoding, Origin",
        "X-Content-Type-Options": "nosniff",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        **rate_headers,
    }
    if extra:
        headers.update(extra)
    return headers


def _send(start_response, environ, rate_headers, status, payload=None, extra=None):
    data = b"" if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = _headers(environ, rate_headers, extra)

    # Gzip content-encoding if accepted and payload is non-trivial (B1)
    if payload is not None and len(data) >= 256 and "gzip" in environ.get("HTTP_ACCEPT_ENCODING", ""):
        compressed = gzip.compress(data)
        if len(compressed) < len(data):
            data = compressed
            headers["Content-Encoding"] = "gzip"

    if payload is None:
        headers.pop("Content-Type", None)
        headers["Content-Length"] = "0"
    else:
        headers["Content-Length"] = str(len(data))

    start_response(f"{status} {_REASONS.get(status, 'OK')}", list(headers.items()))
    return [data]


def _error(start_response, environ, rate_headers, status, title, detail, extra=None):
    return _send(start_response, environ, rate_headers, status, problem(status, title, detail), extra)


def _etag(order):
    published = json.dumps(order.as_json(), sort_keys=True, separators=(",", ":")).encode()
    return '"' + hashlib.sha256(published).hexdigest()[:16] + '"'


def _read_body(environ):
    length = int(environ.get("CONTENT_LENGTH") or 0)
    raw = environ["wsgi.input"].read(length) if length > 0 else b""
    return json.loads(raw or b"null")


def _authorised(environ):
    value = environ.get("HTTP_AUTHORIZATION", "")
    return value.startswith("Bearer ") and bool(value[7:].strip())


def application(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = environ.get("PATH_INFO", "")
    override = environ.get("HTTP_X_HTTP_METHOD_OVERRIDE", "").upper()

    # Documented fallback for constrained clients sending POST (A5)
    if method == "POST" and override in {"PATCH", "DELETE", "PUT"}:
        method = override

    # OPTIONS preflight / discovery (A5, B6) - does not require Authorization
    if method == "OPTIONS":
        parts = path.strip("/").split("/")
        if path == "/orders" or path == "/orders/":
            allow = "GET, POST, OPTIONS"
        elif len(parts) == 2 and parts[0] == "orders":
            allow = "GET, PATCH, DELETE, OPTIONS"
        elif len(parts) == 3 and parts[0] == "orders" and parts[2] in {"cancel", "cancellation"}:
            allow = "POST, OPTIONS"
        else:
            allow = "GET, POST, PATCH, DELETE, OPTIONS"
        return _send(
            start_response,
            environ,
            {"X-RateLimit-Limit": str(RATE_LIMIT), "X-RateLimit-Remaining": str(RATE_LIMIT)},
            204,
            None,
            {"Allow": allow},
        )

    # Content negotiation (B1)
    accept = environ.get("HTTP_ACCEPT", "*/*")
    if "*/*" not in accept and "application/json" not in accept:
        return _error(
            start_response,
            environ,
            {},
            406,
            "Not acceptable",
            "This API only produces application/json.",
        )

    # Per-client rate limit check (B5)
    allowed, rate_headers = _rate_headers(environ)
    if not allowed:
        return _error(
            start_response,
            environ,
            rate_headers,
            429,
            "Rate limit exceeded",
            "Try again after the Retry-After interval.",
        )

    # Bearer token authorization check (B3)
    if not _authorised(environ):
        return _error(
            start_response,
            environ,
            rate_headers,
            401,
            "Unauthorized",
            "Send Authorization: Bearer <token>.",
            {"WWW-Authenticate": "Bearer"},
        )

    try:
        # POST /orders: Create order with Idempotency-Key (A1, B2, C3)
        if method == "POST" and (path == "/orders" or path == "/orders/"):
            key = environ.get("HTTP_IDEMPOTENCY_KEY")
            if not key:
                return _error(
                    start_response,
                    environ,
                    rate_headers,
                    400,
                    "Missing Idempotency-Key",
                    "An Idempotency-Key header is required.",
                )
            try:
                body = _read_body(environ)
                validate(body)
            except (ValueError, json.JSONDecodeError) as exc:
                return _error(start_response, environ, rate_headers, 400, "Malformed order", str(exc))

            order, created = store.create_once(
                Order(body["customerId"], body["items"], body["deliveryAddress"], key)
            )
            if created:
                payment_id = charge_payment(order)
                if payment_id:
                    order.payment_reference, order.status = payment_id, "CONFIRMED"
            return _send(
                start_response,
                environ,
                rate_headers,
                201,
                order.as_json(),
                {"Location": "/orders/" + order.order_id, "Cache-Control": "no-store", "ETag": _etag(order)},
            )

        # GET /orders: Safe list query with filter, sort, and pagination (A1, A3, A4)
        if method == "GET" and (path == "/orders" or path == "/orders/"):
            query = parse_qs(environ.get("QUERY_STRING", ""))
            status = query.get("status", [None])[0]
            if status not in {None, "PAYMENT_PENDING", "CONFIRMED", "CANCELLATION_REQUESTED", "CANCELLED"}:
                return _error(
                    start_response,
                    environ,
                    rate_headers,
                    400,
                    "Invalid status filter",
                    "status is not a known order status.",
                )
            try:
                page = int(query.get("page", ["1"])[0])
                page_size = int(query.get("pageSize", ["20"])[0])
            except ValueError:
                return _error(
                    start_response,
                    environ,
                    rate_headers,
                    400,
                    "Invalid pagination",
                    "page and pageSize must be integers.",
                )
            if page < 1 or not 1 <= page_size <= 100:
                return _error(
                    start_response,
                    environ,
                    rate_headers,
                    400,
                    "Invalid pagination",
                    "page must be positive and pageSize must be 1..100.",
                )
            direction = query.get("sort", ["asc"])[0].lower()
            if direction not in {"asc", "desc"}:
                return _error(
                    start_response,
                    environ,
                    rate_headers,
                    400,
                    "Invalid sort",
                    "sort must be asc or desc.",
                )
            orders = sorted(store.list(status), key=lambda o: o.created_at, reverse=(direction == "desc"))
            start_idx = (page - 1) * page_size
            page_orders = orders[start_idx : start_idx + page_size]
            return _send(
                start_response,
                environ,
                rate_headers,
                200,
                {
                    "orders": [order.as_json() for order in page_orders],
                    "page": page,
                    "pageSize": page_size,
                    "total": len(orders),
                },
                {"Cache-Control": "private, max-age=30"},
            )

        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "orders":
            order_id = parts[1]
            order = store.get(order_id)
            if not order:
                return _error(
                    start_response,
                    environ,
                    rate_headers,
                    404,
                    "Order not found",
                    "No order exists with that id.",
                )

            current_etag = _etag(order)

            # GET /orders/{id}: Read one order with Cache-Control and ETag (A1, B4, C1)
            if method == "GET" and len(parts) == 2:
                headers = {"ETag": current_etag, "Cache-Control": "private, max-age=60"}
                if environ.get("HTTP_IF_NONE_MATCH") == current_etag:
                    return _send(start_response, environ, rate_headers, 304, None, headers)
                return _send(start_response, environ, rate_headers, 200, order.as_json(), headers)

            # PATCH /orders/{id}: Modify delivery address protected by If-Match (A1, C2)
            if method == "PATCH" and len(parts) == 2:
                if environ.get("HTTP_IF_MATCH") != current_etag:
                    return _error(
                        start_response,
                        environ,
                        rate_headers,
                        412,
                        "Precondition failed",
                        "If-Match must equal the current ETag.",
                        {"ETag": current_etag},
                    )
                try:
                    body = _read_body(environ)
                    validate_patch(body)
                except (ValueError, json.JSONDecodeError) as exc:
                    return _error(start_response, environ, rate_headers, 400, "Malformed patch", str(exc))
                order.delivery_address = body["deliveryAddress"]
                return _send(
                    start_response,
                    environ,
                    rate_headers,
                    200,
                    order.as_json(),
                    {"ETag": _etag(order), "Cache-Control": "no-store"},
                )

            # DELETE /orders/{id}: Delete order protected by If-Match (A1, B2, C2)
            if method == "DELETE" and len(parts) == 2:
                if environ.get("HTTP_IF_MATCH") != current_etag:
                    return _error(
                        start_response,
                        environ,
                        rate_headers,
                        412,
                        "Precondition failed",
                        "If-Match must equal the current ETag.",
                        {"ETag": current_etag},
                    )
                store.delete(order.order_id)
                return _send(
                    start_response,
                    environ,
                    rate_headers,
                    204,
                    None,
                    {"Cache-Control": "no-store"},
                )

            # POST /orders/{id}/cancellation or /cancel: Non-CRUD sub-resource (A2, B2)
            if method == "POST" and len(parts) == 3 and parts[2] in {"cancellation", "cancel"}:
                try:
                    cancellation = _read_body(environ)
                    if not isinstance(cancellation, dict) or (
                        "reason" in cancellation and not isinstance(cancellation["reason"], str)
                    ):
                        raise ValueError("Cancellation body must be an object with an optional string reason.")
                except (ValueError, json.JSONDecodeError) as exc:
                    return _error(
                        start_response, environ, rate_headers, 400, "Malformed cancellation", str(exc)
                    )
                if order.status in {"CANCELLATION_REQUESTED", "CANCELLED"}:
                    return _error(
                        start_response,
                        environ,
                        rate_headers,
                        409,
                        "Cancellation already requested",
                        "The order is already being cancelled.",
                    )
                if order.status not in {"PAYMENT_PENDING", "CONFIRMED"}:
                    return _error(
                        start_response,
                        environ,
                        rate_headers,
                        422,
                        "Order cannot be cancelled",
                        "Only pending or confirmed orders may be cancelled.",
                    )
                order.status = "CANCELLATION_REQUESTED"
                return _send(
                    start_response,
                    environ,
                    rate_headers,
                    202,
                    order.as_json(),
                    {"ETag": _etag(order), "Cache-Control": "no-store"},
                )

        return _error(
            start_response, environ, rate_headers, 404, "Not found", "No endpoint matches this URL."
        )
    except Exception:
        return _error(
            start_response,
            environ,
            rate_headers,
            503,
            "Service unavailable",
            "The service could not complete the request safely.",
        )


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    print("Orders service listening on http://127.0.0.1:8001")
    make_server("127.0.0.1", 8001, application).serve_forever()
