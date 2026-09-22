# CampusEats Orders REST Service — Assignment 5

CS543 · Web Services · Assignment 5: HTTP Methods & Headers  
**Team ID:** 5  
**Team Members:** Yash Namdev (20252651066), Arpit Tamrakar (20252651012), Harsh Jain (20252651022), Anupam Rai (20252651011), Saurabh Singh Chauhan (20252651049)

---

## Service Overview

This service implements the complete RESTful HTTP Methods & Headers contract for the **CampusEats Orders** platform using standard Python (WSGI) with zero external dependencies.

### Key HTTP Capabilities
1. **Methods & Semantics (Part A):**
   - Pure GET reads (`GET /orders`, `GET /orders/{id}`) with query string filtering, sorting, and pagination.
   - Resource creation (`POST /orders`) returning `201 Created` with `Location`.
   - Sub-resource non-CRUD action (`POST /orders/{id}/cancellation` and `/orders/{id}/cancel`) returning `202 Accepted`.
   - Modification (`PATCH /orders/{id}`) and removal (`DELETE /orders/{id}`).
   - Method discovery (`OPTIONS`) returning `Allow` headers.
   - Fallback `X-HTTP-Method-Override: PATCH | DELETE | PUT` on POST for constrained clients.
2. **Headers & Content Negotiation (Part B):**
   - Content negotiation: `Accept` header validation (`406 Not Acceptable` if unsupported); gzip compression via `Content-Encoding: gzip` for large payloads when accepted.
   - Bearer token authentication: `Authorization: Bearer <token>` (`401 Unauthorized` with `WWW-Authenticate: Bearer` on failure).
   - Rate limiting: sliding window per-client throttling (`X-RateLimit-Limit: 50`, `X-RateLimit-Remaining`, and `429 Too Many Requests` with `Retry-After`).
   - CORS support: full headers (`Access-Control-Allow-Origin: *`, `Allow-Methods`, `Allow-Headers`, `Expose-Headers`) and unauthenticated `OPTIONS` preflight handling.
   - Security headers: `X-Content-Type-Options: nosniff` and `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
3. **Caching & Concurrency (Part C):**
   - ETag generation: SHA-256 representation fingerprinting on `GET /orders/{id}` with `Cache-Control: private, max-age=60`.
   - Conditional GET: `If-None-Match` returns `304 Not Modified` with zero-byte body.
   - Optimistic concurrency control: `If-Match` required on `PATCH` and `DELETE`; returns `412 Precondition Failed` if stale.
   - Exactly-once order creation: mandatory `Idempotency-Key` on `POST /orders` safely replays the original order on retries.

---

## Running the Service

Start the WSGI server on `http://127.0.0.1:8001`:

```bash
python3 app.py
```

### Running the Test Suite

Run the dependency-free test runner:

```bash
python3 run_tests.py
```

Or using pytest (if installed):

```bash
pytest tests/
```

### Validating the OpenAPI 3.0 Contract

Run the preflight structural validator:

```bash
python3 validate_openapi.py openapi.yaml
```

---

## Submission Artifacts

- `openapi.yaml`: Complete OpenAPI 3.0.3 specification with all methods, query params, headers, and problem response schemas.
- `NOTES.md`: CampusEats method map, request/response headers table, safe-retry plan, labelled HTTP/1.1 exchange, and comprehensive answers to all 8 questions.
- `curl-transcript.txt`: Live-captured `curl -v` verification transcript demonstrating all success, conditional, and failure paths.
- `tests/test_orders.py`: Automated test cases verifying all 15 specification points.
- `CampusEats_Orders_Assignment5.html` / `CampusEats_Orders_Assignment5.pdf`: Formatted report document.
- `CampusEats_Orders_Assignment5.zip`: Complete zip submission package.
