# CS543 Web Services — Assignment 09: Securing the API

Catalogue REST service from Assignment 8 (`GET /items`, `POST /items`, …) secured with
**bcrypt-hashed users**, a **JWT login**, an **`auth`** middleware (authentication) and a
**`requireRole(...)`** middleware (authorization).

## Team

| Roll No. | Name |
|----------|------|
| 20252651022 | Harsh Jain |
| 20252651011 | Anupam Rai |
| 20252651012 | Arpit Tamarakar |
| 20252651066| Yash Namdev |
| 20252651049 | Sourabh Singh Chauhan |

**Demo video & screenshots (Google Drive):**  https://drive.google.com/drive/folders/1sMjgbdkZrH8dx_lrZSM7OXQwh7e4xOUs?usp=sharing
## Setup & run

```bash
npm install
cp .env.example .env          # then put a long random value in JWT_SECRET
# e.g. node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
npm start                     # http://localhost:3000
```

In a second terminal run the Task-6 demo (all five cases + extras):

```bash
npm run demo    
```

### Seeded users (passwords stored only as bcrypt hashes)

| id | username | password (for demo) | role |
|----|----------|---------------------|------|
| 1  | alice    | alice123            | customer   |
| 2  | bob      | bob123              | restaurant |

### Files

| File | Purpose |
|------|---------|
| `server.js` | The secured service: `POST /login`, `auth`, `requireRole`, routes |
| `package.json` | Dependencies: `express`, `jsonwebtoken`, `bcryptjs` (+ `dotenv`) |
| `.env.example` | Config template with a **blank** `JWT_SECRET` (committed) |
| `.gitignore` | Ignores `.env` and `node_modules/` |
| `demo.sh` | curl script reproducing the five cases of Task 6 |
| `demo/demo-output.txt` | Full captured output of `demo.sh` |
| `demo/screenshots/*.png` | Screenshots of each case |

---

## Endpoints

| Method | Path | Guard | Success |
|--------|------|-------|---------|
| GET    | `/`           | none (health check)                        | 200 |
| POST   | `/login`      | none — checks password with `bcrypt.compareSync` | 200 + `{ token }` / 401 |
| GET    | `/items`      | `auth`                                     | 200 |
| GET    | `/items/:id`  | `auth`                                     | 200 / 404 |
| POST   | `/items`      | `auth` → `requireRole('restaurant','admin')` | 201 |
| PUT    | `/items/:id`  | `auth` → `requireRole('restaurant','admin')` | 200 |
| DELETE | `/items/:id`  | `auth` → `requireRole('restaurant','admin')` | 200 |

## Demo results (Task 6)

| # | Request | Result | Screenshot |
|---|---------|--------|------------|
| 1 | `GET /items`, no token | **401** `{"error":"missing token"}` | `demo/screenshots/1-no-token-401.png` |
| 2 | `POST /login` as bob | **200** `{"token":"eyJ…","expiresIn":"1h"}` | `demo/screenshots/2-login-token.png` |
| 3 | `GET /items` with alice's token | **200** list of items | `demo/screenshots/3-with-token-200.png` |
| 4 | `POST /items` with bob's token (restaurant) | **201** `{"id":3,"name":"Masala Dosa","price":149}` | `demo/screenshots/4-restaurant-post-201.png` |
| 5 | `POST /items` with alice's token (customer) | **403** `{"error":"forbidden",…}` | `demo/screenshots/5-customer-post-403.png` |
| + | `POST /login` wrong password | 401 | `demo/screenshots/2b-login-wrong-password-401.png` |
| + | `GET /items` with tampered token | 401 `{"error":"invalid token"}` | `demo/screenshots/6-tampered-token-401.png` |

---

## Answers

### 1. Which routes need only authentication, and which also need a role?

**Authentication only** (any valid token — `customer` or `restaurant`):
- `GET /items` — any logged-in role
- `GET /items/:id` — any logged-in role

**Authentication + role** (`auth` then `requireRole('restaurant','admin')`):
- `POST /items` — roles `restaurant` (or `admin`)
- `PUT /items/:id` — roles `restaurant` (or `admin`)
- `DELETE /items/:id` — roles `restaurant` (or `admin`)

(`POST /login` and `GET /` are public.)

### 2. One 401 and one 403 from the demo

```
$ curl -i http://localhost:3000/items
HTTP/1.1 401 Unauthorized
{"error":"missing token"}
```
**Why 401, not 403:** the request carried no token, so the server doesn't know *who* the caller is. Authentication failed, and authorization was never checked.

```
$ curl -i -X POST http://localhost:3000/items -H "Authorization: Bearer $ALICE" \
       -H 'Content-Type: application/json' -d '{"name":"Free Food","price":0}'
HTTP/1.1 403 Forbidden
{"error":"forbidden","need":["restaurant","admin"],"you":"customer"}
```
**Why 403, not 401:** alice's token is valid, so the server knows who she is. Her role `customer` is simply not allowed to write. That makes it an authorization failure.

### 3. What is inside the JWT, why can the role claim be trusted, and why keep the secret out of the code?

**Payload** (decoded from the demo token):
```json
{ "sub": 2, "username": "bob", "role": "restaurant", "iat": 1794315932, "exp": 1794319532 }
```
`sub` is the user id, `role` is used by `requireRole`, `iat` is the issue time and `exp` is the expiry (from `expiresIn: '1h'`). There is no password or hash in it. The payload is only Base64-encoded, not encrypted, so it must never hold secrets.

**Why the role claim is safe to trust:** the server issued the token itself, and only after `bcrypt.compareSync` succeeded. The token is signed with HMAC-SHA256 using `JWT_SECRET`. On every request `jwt.verify` recomputes the signature and checks `exp`. If a client edits the payload (for example changing `"customer"` to `"restaurant"`), the signature no longer matches and the request gets a 401 (see the tampered-token case). Only someone holding the secret can mint a valid token, so the role in a verified token is the role the server assigned.

**Why the secret must stay out of the code:** the secret is the only thing that stops anyone from forging tokens. If it were hard-coded and pushed to GitHub, anyone reading the repo could sign `{"role":"admin"}` and get full write access. Loading it from `process.env.JWT_SECRET` (via a git-ignored `.env`) keeps it out of version control. It also lets each environment (dev/prod) use its own secret, and the secret can be rotated without changing code. `.env.example` only documents that the variable exists and leaves its value blank.
