# CS543 · Assignment 6 — Honest responses: status codes, errors & validation

| Roll No | Name |
|---------|------|
| 20252651012 | Arpit Tamrakar |
| 20252651022 | Harsh Jain |
| 20252651066 | Yash Namdev |
| 20252651049 | Saurabh Singh Chauhan |
| 20252651011 | Anupam Rai |

**Run:** `npm install && npm start` (port 3000) · **Self-check:** `npm test` (35 checks) · **Transcript:** `bash make_transcript.sh`

Files: `server.js` (the Orders service), `openapi.yaml`, `transcript.txt`, `test.js`, `make_transcript.sh`.
Demo hooks: `payment_token` = `tok_decline` (declined) / `tok_slow` (provider timeout); header `X-Simulate-Fault: db` (internal error).
Seed stock: widget 10, gadget 5, gizmo 0.

---

## 1. Status map

| Endpoint | Success | Failures (status — why) |
|---|---|---|
| `POST /orders` | **201** + `Location` — a new resource now exists | 400 body isn't JSON · 415 body isn't `application/json` · 422 body is JSON but invalid (incl. empty cart) · 409 sku unknown/out of stock — valid request, clashes with current stock · 402 card declined · 406 can't produce requested `Accept` · 429 too many requests · 503 payment provider timed out (transient) · 500 our bug |
| `GET /orders` | **200** — list | 406 · 429 |
| `GET /orders/{id}` | **200** | 404 no such order · 406 · 429 · 500 (e.g. DB failure) |
| `PATCH /orders/{id}` | **200** — updated order | 404 · 400 bad JSON · 422 bad `status`/`address` or empty patch · 409 move not allowed from current status · 429 |
| `DELETE /orders/{id}` | **204** — gone, no body | 404 · 409 order already shipped/delivered · 429 |
| any unknown route | — | 404 `route-not-found` |

**A2 – fixing 200-for-failure:** no handler ever returns a 2xx for a failure. Every failure is built by `problem()` and its status is the HTTP status; there is no `{ "ok": false }` anywhere.
**A3:** `POST /orders` → `201 Created` with `Location: /orders/{id}` (see transcript D1).

## 2. Type catalogue
Stable `type` = `https://cs543.example/problems/<slug>`.

| Slug | Status | Triggered by |
|---|---|---|
| `empty-cart` | 422 | `items` is `[]` |
| `validation-failed` | 422 | any other bad field (qty not an integer ≥ 1, missing sku/address, bad PATCH body…) |
| `item-unavailable` | 409 | sku unknown or stock lower than qty |
| `payment-declined` | 402 | provider declines the card |
| `order-not-found` | 404 | `{id}` doesn't exist |
| `illegal-transition` | 409 | status move not allowed (e.g. `shipped→paid`), or deleting a shipped/delivered order |
| `invalid-json` | 400 | body can't be parsed |
| `unsupported-media` | 415 | body sent with a non-JSON Content-Type |
| `not-acceptable` | 406 | `Accept` is neither JSON nor XML |
| `rate-limited` | 429 | > 30 requests / 10 s for one client |
| `service-unavailable` | 503 | payment provider didn't answer within 1 s |
| `route-not-found` | 404 | unknown path |
| `internal-error` | 500 | anything unexpected |

## 3. One Problem Details body, labelled
```json
{
  "type": "https://cs543.example/problems/illegal-transition",
  "title": "Illegal status transition",
  "status": 409,
  "detail": "Cannot move an order from 'shipped' to 'paid'.",
  "allowed": ["delivered"]
}
```
- `type` – stable URI naming the *kind* of failure (clients branch on this, never on `detail`).
- `title` – short human label, the same every time for that type.
- `status` – repeats the HTTP status.
- `detail` – explanation of this specific occurrence.
- `allowed` – extension member: the moves that *would* be legal.
Sent with `Content-Type: application/problem+json; charset=utf-8`.

## 4. Field-level 422 with two bad fields
Request: `{"items":[{"sku":"widget","qty":-1}],"address":""}`
```json
{
  "type": "https://cs543.example/problems/validation-failed",
  "title": "Request validation failed",
  "status": 422,
  "detail": "2 field(s) failed validation.",
  "errors": [
    { "field": "items[0].qty", "message": "must be an integer >= 1" },
    { "field": "address", "message": "is required and must be a non-empty string" }
  ]
}
```
Validation runs *before* any stock check, payment or write, and collects every error instead of stopping at the first.

## 5. Retry safety
- **Retry-safe (transient):** `503` (payment timeout – stock is released and nothing is charged) and `429`. Both carry `Retry-After`. Wait that long, then resend.
- **Never retry unchanged:** any other 4xx (400, 402, 404, 406, 409, 415, 422) — the same request gets the same answer. Fix the request first.
- **By endpoint:** `GET`, `PATCH` (status target is explicit), `DELETE` are naturally idempotent → safe to retry. `POST /orders` is retry-safe **only with an `Idempotency-Key`**: the same key replays the first result (`Idempotent-Replayed: true`) so a retry can't create a second order; 503/429 results are deliberately *not* remembered, so retrying the same key after a 503 performs the real work.
- `500` – not promised to be safe; retry only a read, or a POST that used an Idempotency-Key.

## 6. Internal errors → clean errors
- Every handler runs inside `handle()` (try/catch). On any thrown error it logs the full stack + message server-side with a random incident id, and returns `500 internal-error` with a fixed sentence and that `incident` id.
- Demo (`X-Simulate-Fault: db`): the DB layer throws `SQLITE_ERROR: no such table: orders_v2 at /srv/app/db.js:42`. `server.log` contains that and the stack; the client only sees the generic detail + incident id. Hidden: SQL/DB error text, table names, file paths, line numbers, stack trace.
- Payment-provider timeout is mapped to `503 service-unavailable` (not 500, not a raw "PAYMENT_TIMEOUT"), with `Retry-After`.
- Malformed JSON from the body parser is mapped to `400 invalid-json` instead of Express's default HTML stack-trace page.

## 7. Content negotiation (JSON vs XML)
`GET /orders/ord_1001` with `Accept: application/json` (or none):
```json
{"id":"ord_1001","status":"shipped","items":[{"sku":"widget","qty":2,"unit_price":9.99},{"sku":"gadget","qty":1,"unit_price":24.5}],"address":"12 Ring Road, Surat","total":44.48,"created_at":"2026-10-13T08:53:32.541Z"}
```
With `Accept: application/xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?><order><id>ord_1001</id><status>shipped</status><items><item><sku>widget</sku><qty>2</qty><unit_price>9.99</unit_price></item><item><sku>gadget</sku><qty>1</qty><unit_price>24.5</unit_price></item></items><address>12 Ring Road, Surat</address><total>44.48</total><created_at>2026-10-13T08:53:32.541Z</created_at></order>
```
`Accept: text/html` → `406 not-acceptable`. Errors are always `application/problem+json`. Every response that has a body states `Content-Type` with `charset=utf-8`.

## D4 – no regressions (from A5)
Idempotency (same key → same order, one stock deduction, also under concurrent requests) and the 1 s payment timeout still hold: see transcript section D4 and the `idempotent replay` / `concurrent same key` / `payment timeout` checks in `npm test`.
