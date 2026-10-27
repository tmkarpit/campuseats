# CampusEats Dishes — CS543 Assignment 7

**Team ID:** 5  
**Team members:** Yash Namdev — 20252651066; Arpit Tamrakar — 20252651012; Harsh Jain — 20252651022; Anupam Rai — 20252651011; Saurabh Singh Chauhan — 20252651049.

## Run

The fastest full setup uses Docker:

```bash
docker compose up
```

Open `http://localhost:4000` for the HTML/CSS client. The GraphQL endpoint and
Apollo Sandbox are at `http://localhost:4000/graphql`.

For a local MySQL installation, run `mysql -u root -p < schema.sql`, copy
`.env.example` to `.env` and set its credentials, then run:

```bash
npm install
npm start
```

## Demonstration

1. Load the page: the four seeded dishes are fetched through the GraphQL query.
2. Enter a name and price, then select **Add dish**.
3. The page sends the `addDish` mutation and reloads the list live. Take one
   screenshot before adding and one after; record a short video of these steps
   for the Google Drive link required by the assignment.

## Required answers

1. We picked the **CampusEats Menu/Dishes service**. It exposes dishes with an
   id, name, price and availability.
2. `available` can be skipped by a query client because GraphQL lets clients
   ask only for the fields they need. `id` cannot be null in the schema
   (`ID!`) because each database row is created with a unique primary key and a
   client needs it to identify the dish. `!` declares that a resolver must
   provide a value for that field.
3. In `dish(id: ID!)`, the `id` argument becomes `WHERE id = ?` in SQL. The
   `Query.dish` resolver runs that SELECT. The `Mutation.addDish` resolver runs
   `INSERT INTO dishes (name, price, available) VALUES (?, ?, ?)` and then a
   SELECT by the generated insert id to return the new object.

## Example operations

```graphql
query { dishes { id name price available } }

mutation {
  addDish(input: { name: "Paneer Roll", price: 90 }) {
    id
    name
    price
  }
}
```

The service deliberately keeps business logic out of resolvers: each resolver
only runs the SQL needed for the requested CRUD operation.
