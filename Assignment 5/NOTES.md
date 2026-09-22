# CampusEats Orders — Assignment 5: HTTP Methods & Headers

**Team ID:** 5  
**Team Members:**
- **Yash Namdev** (Roll / Reg. No.: 20252651066) — *Team Leader*
- **Arpit Tamrakar** (Roll / Reg. No.: 20252651012)
- **Harsh Jain** (Roll / Reg. No.: 20252651022)
- **Anupam Rai** (Roll / Reg. No.: 20252651011)
- **Saurabh Singh Chauhan** (Roll / Reg. No.: 20252651049)

---

## A1–A5: CampusEats Method Map

| Action | Method + URL | Safe | Idempotent | Notes |
|---|---|:---:|:---:|---|
| **List / filter / sort / page orders** | `GET /orders?status=&sort=&page=&pageSize=` | **Yes** | **Yes** | Pure read with query string params (`status`, `sort=asc\|desc`, `page`, `pageSize`). Never mutates server state. |
| **Read an order** | `GET /orders/{orderId}` | **Yes** | **Yes** | Returns cached representation with `ETag` and `Cache-Control`. Supports conditional read via `If-None-Match`. |
| **Create an order** | `POST /orders` | **No** | **No (without key)** | Creates new resource; returns `201 Created` + `Location`. Made retry-safe via mandatory `Idempotency-Key` header. |
| **Change delivery address** | `PATCH /orders/{orderId}` | **No** | **Yes** | Modifies representation. Requires matching `If-Match` ETag to guard against lost updates / clobbering. |
| **Delete an order** | `DELETE /orders/{orderId}` | **No** | **Yes** | Removes resource; returns `204 No Content`. Protected by `If-Match` precondition; repeated delete returns 404/412. |
| **Request order cancellation** | `POST /orders/{orderId}/cancellation`<br>*(alias: `/orders/{orderId}/cancel`)* | **No** | **No** | Non-CRUD action modeled as a POST to a sub-resource, never an imperative RPC URL like `/cancelOrder`. Returns `202 Accepted`. |
| **Discover supported methods** | `OPTIONS /orders`<br>`OPTIONS /orders/{orderId}` | **Yes** | **Yes** | Returns `Allow` header listing permitted verbs (`204 No Content`). Responds to CORS preflight without requiring authentication. |

*Fallback for Constrained Clients (A5):* For restricted clients unable to emit native `PATCH` or `DELETE` verbs, the service accepts `POST` accompanied by `X-HTTP-Method-Override: PATCH` or `DELETE` as a documented fallback only.

---

## D2: Request and Response Headers Table

| Endpoint | Required & Accepted Request Headers | Important Response Headers Set & Purpose |
|---|---|---|
| `GET /orders` | `Authorization: Bearer <token>`<br>`Accept: application/json` *(optional)*<br>`Accept-Encoding: gzip` *(optional)* | `Content-Type: application/json`<br>`Cache-Control: private, max-age=30`<br>`X-RateLimit-Limit`, `X-RateLimit-Remaining`<br>`Content-Encoding: gzip` *(if payload &ge; 256 B and accepted)*<br>`Vary: Accept, Accept-Encoding, Origin`<br>`X-Content-Type-Options: nosniff`<br>`Strict-Transport-Security` |
| `POST /orders` | `Authorization: Bearer <token>`<br>`Content-Type: application/json`<br>`Idempotency-Key: <key>` *(required)*<br>`Accept: application/json` *(optional)* | `Status: 201 Created`<br>`Location: /orders/{orderId}` *(points to new resource)*<br>`ETag: "<hash>"` *(fingerprint of representation)*<br>`Cache-Control: no-store` *(mutation must not be cached)*<br>`X-RateLimit-Limit`, `X-RateLimit-Remaining`<br>CORS & Security headers |
| `GET /orders/{id}` | `Authorization: Bearer <token>`<br>`If-None-Match: "<etag>"` *(optional)*<br>`Accept: application/json` *(optional)* | `Status: 200 OK` or `304 Not Modified`<br>`ETag: "<hash>"`<br>`Cache-Control: private, max-age=60`<br>`Content-Length: 0` *(on 304 without body)*<br>`X-RateLimit-Limit`, `X-RateLimit-Remaining`<br>CORS & Security headers |
| `PATCH /orders/{id}` | `Authorization: Bearer <token>`<br>`Content-Type: application/json`<br>`If-Match: "<etag>"` *(required)*<br>`X-HTTP-Method-Override: PATCH` *(optional)* | `Status: 200 OK` *(or `412 Precondition Failed` if stale)*<br>`ETag: "<new-hash>"` *(updated hash)*<br>`Cache-Control: no-store`<br>`X-RateLimit-Limit`, `X-RateLimit-Remaining`<br>CORS & Security headers |
| `DELETE /orders/{id}` | `Authorization: Bearer <token>`<br>`If-Match: "<etag>"` *(required)*<br>`X-HTTP-Method-Override: DELETE` *(optional)* | `Status: 204 No Content` *(or `412 Precondition Failed`)*<br>`Cache-Control: no-store`<br>`Content-Length: 0`<br>CORS & Security headers |
| `POST /orders/{id}/cancellation` | `Authorization: Bearer <token>`<br>`Content-Type: application/json` | `Status: 202 Accepted` *(or `409 Conflict`, `422 Unprocessable`)*<br>`ETag: "<new-hash>"`<br>`Cache-Control: no-store`<br>CORS & Security headers |
| `OPTIONS /orders` & `/orders/{id}` | `Origin: <origin>` *(browser)*<br>`Access-Control-Request-Method`<br>`Access-Control-Request-Headers` | `Status: 204 No Content`<br>`Allow: GET, POST, OPTIONS` *(or `GET, PATCH, DELETE, OPTIONS`)*<br>`Access-Control-Allow-Origin: *`<br>`Access-Control-Allow-Methods`<br>`Access-Control-Allow-Headers`<br>`Access-Control-Expose-Headers` |

*Global Invariants:*
- All bodies carry `Content-Type: application/json`.
- Demanding unsupported representation returns `406 Not Acceptable`.
- Missing or invalid Bearer token returns `401 Unauthorized` with `WWW-Authenticate: Bearer`.
- Per-client sliding window rate limiting sets `X-RateLimit-Limit: 50` and `X-RateLimit-Remaining`; exhaustion triggers `429 Too Many Requests` with `Retry-After: <seconds>`.
- Security headers `X-Content-Type-Options: nosniff` and `Strict-Transport-Security: max-age=31536000; includeSubDomains` are present on all responses.
- `Date` and `Server` headers are supplied by the WSGI HTTP container. Service is served over HTTPS in production.

---

## C4: The Safe-Retry Plan

| Risky Endpoint | Inherent Risk | Mechanism Applied | Justification & Behaviour |
|---|---|---|---|
| `POST /orders` *(Order Creation)* | Network timeout on request or response; client retries. Duplicate order risks charging student credit card twice and dispatching duplicate kitchen meals. | **Idempotency-Key** | Non-safe, non-idempotent operation. Server atomically maps the unique key to the initial order record. Retrying with identical key returns the original `201 Created` and `Location` without performing duplicate payment or kitchen work. |
| `GET /orders/{orderId}` *(Single Order Read)* | Redundant network transfers and repetitive JSON parsing when representation has not changed. | **If-None-Match (Conditional GET)** | Safe and idempotent read. Client transmits stored ETag. Server evaluates condition: if ETag matches current state, server returns `304 Not Modified` with zero-byte body, saving cellular bandwidth and compute. |
| `PATCH /orders/{orderId}` *(Update Delivery Address)* | Two concurrent editors read order simultaneously. Editor A updates address; Editor B attempts overwrite with stale data, clobbering Editor A's change (lost update problem). | **If-Match (Conditional Write)** | Unsafe, idempotent operation. Client must provide ETag of representation it read. If state changed concurrently, ETag differs and server refuses update with `412 Precondition Failed` rather than overwriting silently. |
| `DELETE /orders/{orderId}` *(Order Cancellation/Removal)* | Multiple deletes or delete racing against concurrent modification. | **If-Match** | Unsafe, idempotent operation. Ensures the resource being deleted is in the exact state expected by the operator. |
| `POST /orders/{id}/cancellation` *(Cancel Sub-Resource)* | Repeated cancellation requests or cancelling already completed/dispatched order. | **State Conflict (409) & Domain Refusal (422)** | Server checks domain lifecycle state: duplicate cancellation returns `409 Conflict` ("The order is already being cancelled"); attempting cancellation when order is already in a non-cancellable state returns `422 Unprocessable Content`. |

---

## A6: Complete HTTP Exchange

Below is an authentic, full HTTP exchange between client and server, with every logical section explicitly labelled.

### Complete Client Request

```http
POST /orders HTTP/1.1
Host: 127.0.0.1:8001
User-Agent: curl/7.88.1
Accept: application/json
Content-Type: application/json
Authorization: Bearer demo-token
Idempotency-Key: a5-demo-key-991
Content-Length: 111

{"customerId":"stu-102","items":[{"menuItemId":"menu-42","quantity":2}],"deliveryAddress":"Hostel A, Room 210"}
```

#### Request Breakdown and Labels:
1. **Request Line:** `POST /orders HTTP/1.1`
   - *Method:* `POST` (resource creation)
   - *Request-URI:* `/orders` (collection endpoint)
   - *HTTP Version:* `HTTP/1.1` (persistent connections, mandatory Host header)
2. **Host Header:** `Host: 127.0.0.1:8001` (specifies target domain and port, required in HTTP/1.1)
3. **Request Headers:**
   - `User-Agent: curl/7.88.1` (client software identification)
   - `Accept: application/json` (content negotiation: client requests JSON)
   - `Content-Type: application/json` (media type of the request payload)
   - `Authorization: Bearer demo-token` (bearer token authentication credential)
   - `Idempotency-Key: a5-demo-key-991` (unique retry token ensuring exactly-once processing)
   - `Content-Length: 111` (exact byte length of request body)
4. **Empty Line:** CRLF (`\r\n`) separating headers from payload
5. **Request Body:** `{"customerId":"stu-102","items":[{"menuItemId":"menu-42","quantity":2}],"deliveryAddress":"Hostel A, Room 210"}` (JSON object fulfilling `CreateOrderRequest` schema)

---

### Complete Server Response

```http
HTTP/1.0 201 Created
Content-Type: application/json
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Authorization, Content-Type, Idempotency-Key, If-None-Match, If-Match, X-HTTP-Method-Override, Accept, Accept-Encoding
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
Access-Control-Expose-Headers: Location, ETag, X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After, Content-Encoding
Vary: Accept, Accept-Encoding, Origin
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 49
Location: /orders/ord-cff77796afcb
Cache-Control: no-store
ETag: "89a179fcd47ae96b"
Content-Length: 196
Server: WSGIServer/0.2 CPython/3.12.3
Date: Tue, 22 Sep 2026 03:15:20 GMT

{"id":"ord-cff77796afcb","customerId":"stu-102","items":[{"menuItemId":"menu-42","quantity":2}],"deliveryAddress":"Hostel A, Room 210","status":"PAYMENT_PENDING","createdAt":"2026-09-22T03:15:20.124501+00:00"}
```

#### Response Breakdown and Labels:
1. **Status Line:** `HTTP/1.0 201 Created`
   - *HTTP Version:* `HTTP/1.0` (emitted by the Python `wsgiref.simple_server` development container)
   - *Status Code:* `201` (resource created successfully)
   - *Reason Phrase:* `Created`
2. **Response Headers:**
   - `Content-Type: application/json` (media type of body representation)
   - `Location: /orders/ord-cff77796afcb` (canonical URI pointing to newly created order)
   - `ETag: "89a179fcd47ae96b"` (SHA-256 fingerprint of created representation for caching & concurrency)
   - `Cache-Control: no-store` (instructs caches never to cache response of creation action)
   - `X-RateLimit-Limit: 50` & `X-RateLimit-Remaining: 49` (client rate limit tracking)
   - `Access-Control-Allow-Origin: *` & related CORS headers (enables cross-origin browser access)
   - `X-Content-Type-Options: nosniff` (security: prevents MIME sniffing attacks)
   - `Strict-Transport-Security` (security: enforces HTTPS in modern browsers)
   - `Server` & `Date` (transport-level metadata generated by the server container)
   - `Content-Length: 196` (byte size of JSON payload)
3. **Empty Line:** CRLF (`\r\n`) separating headers from payload
4. **Response Body:** Full JSON serialized order entity including generated `id`, `status: "PAYMENT_PENDING"`, and `createdAt` timestamp.

*Note on HTTP Versions:* The client issues an `HTTP/1.1` request line (allowing Host headers, pipelining, and persistent connections). The Python WSGI reference server answers with `HTTP/1.0` (as standard for `wsgiref.simple_server` close-on-finish semantics). When reverse-proxied behind Nginx or Envoy in production, this becomes end-to-end `HTTP/1.1` or `HTTP/2` over TLS.

---

## Required Answers to Assignment Questions

### 1. For three of your endpoints, give the method, the success status, and the single response header that matters most — and why.

1. **`POST /orders`**  
   - *Success Status:* `201 Created`  
   - *Single Most Critical Header:* `Location: /orders/{orderId}`  
   - *Why:* The client does not know the server-assigned identifier ahead of time. The `Location` header is the standardized REST mechanism communicating where the newly minted resource lives, allowing the client to bookmark, inspect, track, or redirect to the new order.
2. **`GET /orders/{orderId}`**  
   - *Success Status:* `200 OK` (or `304 Not Modified`)  
   - *Single Most Critical Header:* `ETag: "<hex-hash>"`  
   - *Why:* The entity tag uniquely fingerprints this exact version of the order representation. It powers client-side caching via `If-None-Match` (avoiding redundant data transfer) and optimistic concurrency control for subsequent updates via `If-Match` (preventing lost updates).
3. **`DELETE /orders/{orderId}`**  
   - *Success Status:* `204 No Content`  
   - *Single Most Critical Header:* `Cache-Control: no-store`  
   - *Why:* Because a 204 response carries no entity body, intermediate proxies and browser caches must be explicitly instructed not to retain or reuse any previously cached representations of this now-deleted resource.

---

### 2. Which of your endpoints are safe, and which are idempotent? Which one is neither, and how did you make it retry-safe?

- **Safe Endpoints (do not alter resource state):**
  - `GET /orders`
  - `GET /orders/{orderId}`
  - `OPTIONS /orders`
  - `OPTIONS /orders/{orderId}`
  *All safe endpoints are naturally idempotent.*
- **Idempotent Endpoints (repeating the call produces the exact same resultant server state):**
  - `GET /orders`
  - `GET /orders/{orderId}`
  - `OPTIONS /orders`
  - `OPTIONS /orders/{orderId}`
  - `PATCH /orders/{orderId}` (applying the same update representation multiple times leaves the resource in the exact same updated state)
  - `DELETE /orders/{orderId}` (once deleted, repeating the deletion has no further state effect on the resource store)
- **Endpoints that are Neither Safe nor Idempotent:**
  - `POST /orders` (creating an order modifies state; repeated calls create distinct orders and duplicate payment charges).
  - `POST /orders/{orderId}/cancellation` (initiates state transition from confirmed to cancellation requested).
- **How `POST /orders` was made Retry-Safe:**
  By requiring the client to supply an `Idempotency-Key` header with every order creation request. The server's `OrderStore.create_once()` atomically checks whether an order with that idempotency key was already created. If seen previously, the service skips item creation and payment processing entirely and returns the original `201 Created` response with the original `Location` and representation. If a mobile network drops the connection after the server accepted the order, the client can safely re-send the request with the identical key without charging the student twice or preparing duplicate food.

---

### 3. Show one ETag from your service, the request that returns 304, and the write that returns 412. What does each save or prevent?

- **Concrete ETag Example:** `"89a179fcd47ae96b"` (generated as a SHA-256 digest of the canonical order representation).

#### Request Returning 304 Not Modified:
```http
GET /orders/ord-cff77796afcb HTTP/1.1
Host: 127.0.0.1:8001
Authorization: Bearer demo-token
If-None-Match: "89a179fcd47ae96b"
```
- *Response:* `HTTP/1.0 304 Not Modified` with `Content-Length: 0` (no response body).
- *What it Saves:* Saves bandwidth, battery, network latency, and client CPU cycles by skipping the transmission and JSON deserialization of an entity representation the client already has cached locally.

#### Write Returning 412 Precondition Failed:
```http
PATCH /orders/ord-cff77796afcb HTTP/1.1
Host: 127.0.0.1:8001
Authorization: Bearer demo-token
Content-Type: application/json
If-Match: "stale-etag-99999"

{"deliveryAddress":"Faculty Lounge 104"}
```
- *Response:* `HTTP/1.0 412 Precondition Failed`
- *What it Prevents:* Prevents the **Lost Update Problem**. If two dispatchers or customers open the same order concurrently, and Dispatcher A updates the delivery instructions while Dispatcher B was reviewing the older version, Dispatcher B’s write is rejected with 412 because their `If-Match` ETag is stale. Dispatcher B must re-read the updated state rather than silently overwriting Dispatcher A's change.

---

### 4. You return 422 for one case and 400 for another. Give the exact request that triggers each, and explain the difference.

#### Request Triggering 400 Bad Request:
```http
POST /orders HTTP/1.1
Host: 127.0.0.1:8001
Authorization: Bearer demo-token
Idempotency-Key: test-bad-400
Content-Type: application/json

{"customerId":"stu-102"}
```
- *Trigger:* The request body is missing mandatory contract fields (`items` and `deliveryAddress`).
- *Response:* `400 Bad Request` with `{"type":"about:blank","title":"Malformed order","status":400,"detail":"Missing required field(s): items, deliveryAddress."}`.

#### Request Triggering 422 Unprocessable Content:
```http
POST /orders/ord-cff77796afcb/cancellation HTTP/1.1
Host: 127.0.0.1:8001
Authorization: Bearer demo-token
Content-Type: application/json

{"reason":"Found alternative food"}
```
*(Assuming order `ord-cff77796afcb` was already marked `CANCELLED` or is in a terminal non-cancellable state).*
- *Trigger:* The JSON syntax and schema are 100% valid, but the business logic rejects the operation because business rules forbid cancelling an order that is already completed or cancelled.
- *Response:* `422 Unprocessable Content` with `{"type":"about:blank","title":"Order cannot be cancelled","status":422,"detail":"Only pending or confirmed orders may be cancelled."}`.

#### Explanation of Difference:
- **400 Bad Request** signals a **syntactic or schema defect**: the message cannot be processed because required fields are absent, types are incorrect, or the JSON is invalid. The fault lies in the structure of the request message itself.
- **422 Unprocessable Content** signals a **semantic or domain rule refusal**: the request payload is syntactically flawless and satisfies the schema, but internal business constraints or entity lifecycle rules prohibit executing the requested transition in the resource's current state.

---

### 5. A browser page on another origin calls your API and is blocked — yet your server logs show a 200. Who blocked it, and which response header fixes it?

- **Who Blocked It:**  
  The **client’s web browser** blocked the page's JavaScript code from reading the response. Under the browser's **Same-Origin Policy (SOP)**, web applications on origin `A` (e.g. `https://campusportal.edu`) cannot read data retrieved from origin `B` (e.g. `http://api.campuseats.internal:8001`) unless origin `B` explicitly permits it. The browser dispatches the HTTP request, the server executes it and logs `200 OK`, but when the response arrives at the browser without the appropriate cross-origin authorization headers, the browser hides the response from the script and throws a JavaScript DOMException / NetworkError.
- **Which Response Header Fixes It:**  
  The `Access-Control-Allow-Origin` header fixes it (e.g., `Access-Control-Allow-Origin: *` or echoing the specific requesting origin `Access-Control-Allow-Origin: https://campusportal.edu`). For complex requests involving custom headers (such as `Authorization` or `Idempotency-Key`), the server must additionally answer the browser's preflight `OPTIONS` request with `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers`.

---

### 6. Name one response where you set Cache-Control to allow caching and one where you must use no-store. Why each?

1. **Allow Caching (`Cache-Control: private, max-age=60`):**  
   - *Where:* `GET /orders/{orderId}`.  
   - *Why:* An existing order’s details change infrequently once submitted. Allowing the student’s browser to cache the representation for 60 seconds eliminates repetitive round-trips while checking order details. The directive `private` guarantees that shared intermediate proxy caches (like campus gateways or CDNs) will not store the order, preventing sensitive student dietary and delivery information from leaking to other campus users.
2. **Must Use `no-store` (`Cache-Control: no-store`):**  
   - *Where:* `POST /orders`, `PATCH /orders/{orderId}`, `DELETE /orders/{orderId}`, and `POST /orders/{id}/cancellation`.  
   - *Why:* `no-store` forbids any cache (private or shared) from persisting any part of the request or response. For order placement and cancellation, caching the response could lead to stale financial status displays, accidental duplicate transactions, or intermediate proxies replaying stale cached results rather than communicating directly with the transactional authority.

---

### 7. Your search endpoint is a GET. When would POST be the right choice instead, and what do you give up by switching?

- **When POST Would Be the Right Choice:**  
  1. *Query Complexity and Size:* When search criteria exceed URL length limits (typically ~2,000 characters in practical proxy configurations). For example, querying orders matching a list of hundreds of specific menu item UUIDs, polygon delivery coordinates, or complex nested JSON filter trees.  
  2. *Data Sensitivity:* Query parameters appear in browser history, proxy access logs, and `Referer` headers. If the search filter contains sensitive data (e.g., medical dietary restrictions, student payment tokens, or PII), passing it in a TLS-encrypted request body via POST keeps it out of URL access logs.
- **What You Give Up by Switching to POST:**  
  1. *Idempotent Caching:* Standard HTTP caches, CDNs, and browser forward-caches automatically cache GET requests; they do not cache POST requests by default.  
  2. *Bookmarkability and Shareability:* Users and campus runners cannot bookmark, copy-paste, or share search query URLs.  
  3. *Browser History and Navigation:* Hitting the "Back" or "Refresh" button on a POST search causes browser warning dialogs ("Form submission will be repeated") or accidental duplicate operations.  
  4. *Pre-fetching & Crawling:* Search engines and client pre-fetchers can safely pre-load GET reads but will never pre-fetch POST.

---

### 8. Location appears on a 201 and on a 3xx. What does it point to in each case?

- **On a `201 Created` Response:**  
  `Location` points to the **canonical URI of the newly created resource** (e.g. `Location: /orders/ord-cff77796afcb`). It tells the client: *"Your creation succeeded; here is the persistent identity and address where the new resource can be retrieved, monitored, or modified in the future."*
- **On a `3xx Redirection` Response (e.g. 301, 302, 303, 307, 308):**  
  `Location` points to the **target URI to which the client should redirect or re-issue its request next**. For instance, in a `303 See Other` response following form processing, `Location` specifies the URL the client should immediately request via `GET` to view the outcome, implementing the Post/Redirect/Get pattern.
