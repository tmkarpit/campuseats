# CampusEats Orders — Assignment 4

**Student:** Yash Namdev  
**Roll / Registration No.:** 20252651066  
**Team ID:** 5  
**Chosen service:** Orders (not Payments)

## Part A — resource design

### A2. SOAP-style starting operations

`placeOrder(customerId, items, deliveryAddress)`, `getOrder(orderId)`,
`listOrders(status)`, and `cancelOrder(orderId, reason)` are the operations that
would have appeared in the earlier SOAP interface.

### A4. Resource table

| Method | URL | What it does | Success | Failure codes |
|---|---|---|---:|---|
| POST | `/orders` | Creates an order | 201 | 400, 503 |
| GET | `/orders/{orderId}` | Returns one order | 200 | 404 |
| GET | `/orders?status=CONFIRMED` | Lists orders filtered by state | 200 | 400 |
| POST | `/orders/{orderId}/cancellation` | Requests asynchronous cancellation | 202 | 400, 404, 409, 422 |

### A5. Hard mapping choice

`cancelOrder(orderId, reason)` maps less comfortably than the other operations:
it looks like an imperative verb. I modelled it as creation of a cancellation
sub-resource at `/orders/{orderId}/cancellation`, because cancellation has its
own request, state, and asynchronous processing. I rejected `/cancelOrder` as
an RPC URL because it exposes an action instead of a durable noun. I also
rejected `DELETE /orders/{orderId}` because the order must remain auditable and
cancellation is not immediate deletion.

## Part D — dependency fallback

`PAYMENTS_URL` is read only from the environment. A payment POST uses a 2-second
timeout and at most three attempts with exponential backoff plus jitter; the
same `Idempotency-Key` accompanies it. HTTP 4xx responses are never retried.
If Payments is unavailable or not configured, the order is accepted with
`PAYMENT_PENDING` rather than pretending it is paid. This preserves the order
and prevents delivery from treating an uncharged order as confirmed; a worker
can reconcile the pending payment later.

## Required comparison answers

### 1. WSDL and OpenAPI line count

The actual Assignment 3 TrustPay partner WSDL (`partner.wsdl`) has **115** lines;
`openapi.yaml` has **125** lines. The 10-line difference is mainly paths, HTTP methods/statuses, JSON
representations and reusable problem responses, while WSDL concentrates on
operations, messages, bindings and XML types. The WSDL declared a SOAP binding
and `SOAPAction`; OpenAPI does not need either because HTTP verbs, media types,
and the server URL do that work.

### 2. Fault to problem response

The actual Assignment 3 SOAP fault is `<faultcode>soap:Client</faultcode>` with
`<faultstring>Payment declined</faultstring>` and the `PaymentFault` code
`CARD_DECLINED`. Its REST replacement is `422 Unprocessable Content` with
`{"type":"about:blank","title":"Payment declined","status":422,"detail":"Payment was declined. Please use another payment method."}`.
Sending the error inside `200 OK` makes caches, gateways, monitoring and retry
logic see success, so they cannot apply normal HTTP failure handling.

### 3. Publish, find, bind

In Assignment 3, publish was the TrustPay entry in the partner catalogue, find
was checkout looking up the active payment-gateway record and WSDL pointer, and
bind was the generated SOAP client using the endpoint in that record. In this
REST service, publish remains the OpenAPI document; find becomes deployment
configuration through `PAYMENTS_URL`; bind becomes an ordinary HTTP client using
the documented method, path and JSON media type.

### 4. Validation responsibility

`validate()` in `app.py` now performs the request checks before any body fields
are used. Without it, a body missing `items` could raise a server error or result
in an invalid empty order instead of a clear `400 Malformed order` response.

### 5. Where SOAP could still be preferable

I would still choose SOAP for the TrustPay payment edge from Assignment 3, which
requires a strict message contract, message-level credentials, and predictable
fault structures. The guarantee being purchased is an authenticated,
integrity-protected partner message with a stable enterprise contract, rather
than merely a convenient JSON-over-HTTP API.
