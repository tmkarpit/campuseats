const fs = require('fs');
const path = require('path');
const express = require('express');
const cors = require('cors');
const { ApolloServer } = require('@apollo/server');
const { expressMiddleware } = require('@as-integrations/express4');
const pool = require('./db');

const typeDefs = fs.readFileSync(path.join(__dirname, 'schema.graphql'), 'utf8');
const toDish = (row) => ({ ...row, price: Number(row.price), available: Boolean(row.available) });

const resolvers = {
  Query: {
    dishes: async () => {
      const [rows] = await pool.execute('SELECT id, name, price, available FROM dishes ORDER BY id');
      return rows.map(toDish);
    },
    dish: async (_, { id }) => {
      const [rows] = await pool.execute('SELECT id, name, price, available FROM dishes WHERE id = ?', [id]);
      return rows[0] ? toDish(rows[0]) : null;
    }
  },
  Mutation: {
    addDish: async (_, { input }) => {
      const available = input.available ?? true;
      const [result] = await pool.execute(
        'INSERT INTO dishes (name, price, available) VALUES (?, ?, ?)',
        [input.name.trim(), input.price, available]
      );
      const [rows] = await pool.execute('SELECT id, name, price, available FROM dishes WHERE id = ?', [result.insertId]);
      return toDish(rows[0]);
    }
  }
};

async function start() {
  // Docker starts the database and application together; wait briefly for MySQL
  // instead of failing if the database has not finished initialising yet.
  let connected = false;
  for (let attempt = 1; attempt <= 15; attempt += 1) {
    try {
      await pool.query('SELECT 1');
      connected = true;
      break;
    } catch (error) {
      console.log(`Waiting for MySQL (${attempt}/15)…`);
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }
  if (!connected) throw new Error('MySQL was not reachable after 30 seconds.');
  const server = new ApolloServer({ typeDefs, resolvers });
  await server.start();

  const app = express();
  app.use(express.static(path.join(__dirname, 'public')));
  app.use('/graphql', cors(), express.json(), expressMiddleware(server));
  const port = Number(process.env.PORT || 4000);
  app.listen(port, () => {
    console.log(`CampusEats Dishes UI: http://localhost:${port}`);
    console.log(`GraphQL endpoint:       http://localhost:${port}/graphql`);
  });
}

start().catch((error) => {
  console.error('Could not start CampusEats GraphQL service:', error.message);
  process.exit(1);
});
