# HTTP Log

Public API used: JSONPlaceholder, a read-only fake JSON API at `https://jsonplaceholder.typicode.com`.

## Request 1: Get one post

Command:

```bash
curl -i https://jsonplaceholder.typicode.com/posts/1
```

HTTP request:

```http
GET /posts/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
```

HTTP response:

```http
HTTP/1.1 200 OK
Date: Sat, 15 Aug 2026 11:22:23 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 292
Connection: keep-alive
access-control-allow-credentials: true
Cache-Control: max-age=43200
etag: W/"124-yiKdLzqO5gfBrJFrcdJ8Yq0LGnU"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
Server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 999
x-ratelimit-reset: 1785194663
Age: 2836
Accept-Ranges: bytes
cf-cache-status: HIT
CF-RAY: a2b7d2383a31c617-BOM
alt-svc: h3=":443"; ma=86400

{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto"
}
```

Note: `200 OK` means the request succeeded. `Content-Type: application/json; charset=utf-8` means the response body is JSON text encoded with UTF-8.

## Request 2: Get one comment

Command:

```bash
curl -i https://jsonplaceholder.typicode.com/comments/1
```

HTTP request:

```http
GET /comments/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
```

HTTP response:

```http
HTTP/1.1 200 OK
Date: Sat, 15 Aug 2026 11:22:15 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 268
Connection: keep-alive
access-control-allow-credentials: true
Cache-Control: max-age=43200
etag: W/"10c-KJ4I9RM/+33TKdV8CFsIvqsDSP0"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
Server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 987
x-ratelimit-reset: 1786773163
Age: 19818
Accept-Ranges: bytes
cf-cache-status: HIT
CF-RAY: a2b7d208dcc0b333-BOM
alt-svc: h3=":443"; ma=86400

{
  "postId": 1,
  "id": 1,
  "name": "id labore ex et quam laborum",
  "email": "Eliseo@gardner.biz",
  "body": "laudantium enim quasi est quidem magnam voluptate ipsam eos\ntempora quo necessitatibus\ndolor quam autem quasi\nreiciendis et nam sapiente accusantium"
}
```

Note: `200 OK` means the comment resource was found and returned. The JSON content type tells the client to parse the body as a JSON object.

## Request 3: Get one user

Command:

```bash
curl -i https://jsonplaceholder.typicode.com/users/1
```

HTTP request:

```http
GET /users/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
```

HTTP response:

```http
HTTP/1.1 200 OK
Date: Sat, 15 Aug 2026 11:22:22 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 509
Connection: keep-alive
access-control-allow-credentials: true
Cache-Control: max-age=43200
etag: W/"1fd-+2Y3G3w049iSZtw5t1mzSnunngE"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
Server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 999
x-ratelimit-reset: 1786754590
Age: 9493
Accept-Ranges: bytes
cf-cache-status: HIT
CF-RAY: a2b7d23158eb6470-BOM
alt-svc: h3=":443"; ma=86400

{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "suite": "Apt. 556",
    "city": "Gwenborough",
    "zipcode": "92998-3874",
    "geo": {
      "lat": "-37.3159",
      "lng": "81.1496"
    }
  },
  "phone": "1-770-736-8031 x56442",
  "website": "hildegard.org",
  "company": {
    "name": "Romaguera-Crona",
    "catchPhrase": "Multi-layered client-server neural-net",
    "bs": "harness real-time e-markets"
  }
}
```

Note: `200 OK` means the user record exists. The JSON content type shows that the nested address and company fields are structured JSON data.

## Request 4: Get one todo item

Command:

```bash
curl -i https://jsonplaceholder.typicode.com/todos/1
```

HTTP request:

```http
GET /todos/1 HTTP/1.1
Host: jsonplaceholder.typicode.com
```

HTTP response:

```http
HTTP/1.1 200 OK
Date: Sat, 15 Aug 2026 11:22:21 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 83
Connection: keep-alive
access-control-allow-credentials: true
Cache-Control: max-age=43200
etag: W/"53-hfEnumeNh6YirfjyjaujcOPPT+s"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
Server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 999
x-ratelimit-reset: 1783572003
Age: 20096
Accept-Ranges: bytes
cf-cache-status: HIT
CF-RAY: a2b7d22ccd8ffc8b-BOM
alt-svc: h3=":443"; ma=86400

{
  "userId": 1,
  "id": 1,
  "title": "delectus aut autem",
  "completed": false
}
```

Note: `200 OK` means the todo resource was returned successfully. The JSON content type means the boolean value `completed` should be read as JSON, not plain text.

## Request 5: Deliberate 404 for a missing post

Command:

```bash
curl -i https://jsonplaceholder.typicode.com/posts/9999
```

HTTP request:

```http
GET /posts/9999 HTTP/1.1
Host: jsonplaceholder.typicode.com
```

HTTP response:

```http
HTTP/1.1 404 Not Found
Date: Sat, 15 Aug 2026 11:22:20 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 2
Connection: keep-alive
access-control-allow-credentials: true
Cache-Control: max-age=43200
etag: W/"2-vyGp6PvFo4RvsFtPoIWeCReyIC8"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
Server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 999
x-ratelimit-reset: 1786792963
cf-cache-status: EXPIRED
CF-RAY: a2b7d2207efea6ad-BOM
alt-svc: h3=":443"; ma=86400

{}
```

Note: `404 Not Found` means the server understood the request but no resource exists at `/posts/9999`. The API still returns `application/json`, so the empty error body is represented as the JSON object `{}`.
