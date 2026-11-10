// CS543 Web Services — Assignment 09: Securing the API
// Catalogue service from Assignment 8 (GET /items, POST /items, ...) secured with
// JWT authentication (auth) and role-based authorization (requireRole).

require('dotenv').config();
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

// ---------------------------------------------------------------------------
// 5. Secrets & config — the secret comes from the environment, never the code
// ---------------------------------------------------------------------------
const SECRET = process.env.JWT_SECRET;
const PORT = process.env.PORT || 3000;
const TOKEN_TTL = process.env.JWT_EXPIRES_IN || '1h';

if (!SECRET) {
  console.error('FATAL: JWT_SECRET is not set. Copy .env.example to .env and fill it in.');
  process.exit(1);
}

const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// 1. Users & hashing — two seeded users with different roles.
//    Only bcrypt hashes are kept in memory; plain-text passwords are never stored.
// ---------------------------------------------------------------------------
const users = [
  { id: 1, username: 'alice', role: 'customer',   passwordHash: bcrypt.hashSync('alice123', 10) },
  { id: 2, username: 'bob',   role: 'restaurant', passwordHash: bcrypt.hashSync('bob123', 10) },
];

// Catalogue data (same in-memory store as Assignment 8)
let items = [
  { id: 1, name: 'Margherita Pizza', price: 299 },
  { id: 2, name: 'Paneer Tikka',     price: 249 },
];
let nextId = 3;

// ---------------------------------------------------------------------------
// 2. Login — POST /login → JWT { sub, username, role } with an expiry
// ---------------------------------------------------------------------------
app.post('/login', (req, res) => {
  const { username, password } = req.body || {};
  const user = users.find(u => u.username === username);

  if (!user || !password || !bcrypt.compareSync(password, user.passwordHash)) {
    return res.status(401).json({ error: 'invalid username or password' });
  }

  const token = jwt.sign(
    { sub: user.id, username: user.username, role: user.role },
    SECRET,
    { expiresIn: TOKEN_TTL }
  );
  res.json({ token, expiresIn: TOKEN_TTL });
});

// ---------------------------------------------------------------------------
// 3. Authentication — who are you?
//    Reads "Authorization: Bearer <token>", verifies it, 401 if missing/invalid/expired.
// ---------------------------------------------------------------------------
function auth(req, res, next) {
  const [scheme, token] = (req.get('Authorization') || '').split(' ');
  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({ error: 'missing token' });
  }
  try {
    req.user = jwt.verify(token, SECRET);
    next();
  } catch (err) {
    const msg = err.name === 'TokenExpiredError' ? 'token expired' : 'invalid token';
    res.status(401).json({ error: msg });
  }
}

// ---------------------------------------------------------------------------
// 4. Authorization — may you?  403 for an authenticated user without the role.
// ---------------------------------------------------------------------------
const requireRole = (...allowed) => (req, res, next) =>
  allowed.includes(req.user.role)
    ? next()
    : res.status(403).json({ error: 'forbidden', need: allowed, you: req.user.role });

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------
// Public health check (no token needed)
app.get('/', (req, res) => res.json({ service: 'Catalogue', status: 'ok' }));

// Read routes — authentication only (any logged-in role)
app.get('/items', auth, (req, res) => res.json(items));

app.get('/items/:id', auth, (req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'item not found' });
  res.json(item);
});

// Write routes — authentication + role 'restaurant' (or 'admin')
app.post('/items', auth, requireRole('restaurant', 'admin'), (req, res) => {
  const { name, price } = req.body || {};
  if (!name || typeof price !== 'number') {
    return res.status(400).json({ error: 'name (string) and price (number) are required' });
  }
  const item = { id: nextId++, name, price };
  items.push(item);
  res.status(201).json(item);
});

app.put('/items/:id', auth, requireRole('restaurant', 'admin'), (req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'item not found' });
  const { name, price } = req.body || {};
  if (name !== undefined) item.name = name;
  if (price !== undefined) item.price = price;
  res.json(item);
});

app.delete('/items/:id', auth, requireRole('restaurant', 'admin'), (req, res) => {
  const idx = items.findIndex(i => i.id === Number(req.params.id));
  if (idx === -1) return res.status(404).json({ error: 'item not found' });
  const [removed] = items.splice(idx, 1);
  res.json(removed);
});

app.listen(PORT, () => console.log(`Catalogue API listening on http://localhost:${PORT}`));
