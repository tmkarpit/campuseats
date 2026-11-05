# CampusEats Menu — REST API (Node + Express)

**Run:** `npm install && node server.js` → open http://localhost:3000

**Team (CS543 Assignment 8)**

| Roll No. | Name |
|----------|------|
| _roll no._ | _name_ |
| _roll no._ | _name_ |

Demo video: _<Google Drive link>_ · Screenshots: `screenshots/1_before_post.png`, `screenshots/2_after_post.png`

---

## 1. Which CampusEats service, and what are its routes?

I picked the **Menu / Catalogue** service of CampusEats (the college canteen app). In the CampusEats service design it is the **Catalogue** service: it owns restaurants, menus and prices, and no other service touches that data. Each dish has `id`, `name`, `price`, `available`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/items` | list the whole menu |
| GET | `/items/:id` | fetch one dish |
| POST | `/items` | add a dish |

Data lives in an in-memory array (4 seed dishes), so it resets when the server restarts.

## 2. Status codes

| Code | When |
|------|------|
| **200 OK** | `GET /items` and `GET /items/:id` when the dish exists |
| **201 Created** | `POST /items` succeeded; the body is the new dish with its id |
| **404 Not Found** | `GET /items/:id` for an id that does not exist (`{"error":"not found"}`) |
| **422 Unprocessable Entity** | `POST /items` with a missing/blank `name` or a missing/non-numeric `price` |

## 3. `req.params` vs `req.body`, and why `express.json()`?

- **`req.params.id`** is used in `GET /items/:id`. The id is part of the URL path (`/items/3`), so Express puts it in `req.params`.
- **`req.body`** is used in `POST /items`. The client sends the new dish as a JSON body, and the route reads `name`, `price` and `available` from it.
- **Why `express.json()`?** The request body arrives as a raw stream of text. Without the `express.json()` middleware, Express does not parse it and `req.body` is `undefined`. The middleware reads the body when the `Content-Type` is `application/json` and fills `req.body` with the parsed object.
