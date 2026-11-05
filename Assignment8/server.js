// server.js -- CampusEats Menu REST API (Node + Express)
const express = require('express');
const app = express();

app.use(express.json());            // fill req.body from JSON request bodies
app.use(express.static('public'));  // serve the web page

// the menu -- in-memory array is the source of truth
let items = [
  { id: 1, name: 'Veg Thali',   price: 90, available: true  },
  { id: 2, name: 'Paneer Roll', price: 70, available: true  },
  { id: 3, name: 'Samosa',      price: 15, available: true  },
  { id: 4, name: 'Cold Coffee', price: 40, available: false },
];
let nextId = 5;

// GET /items -- list the whole menu  -> 200
app.get('/items', (req, res) => {
  res.json(items);
});

// GET /items/:id -- one dish -> 200, or 404 if absent
app.get('/items/:id', (req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'not found' });
  res.json(item);
});

// POST /items -- add a dish -> 201, or 422 if a required field is missing
app.post('/items', (req, res) => {
  const { name, price, available } = req.body || {};
  if (!name || !String(name).trim() || price === undefined || price === '' || isNaN(Number(price))) {
    return res.status(422).json({ error: 'name and a numeric price are required' });
  }
  const item = {
    id: nextId++,
    name: String(name).trim(),
    price: Number(price),
    available: available === undefined ? true : available === true || available === 'true',
  };
  items.push(item);
  res.status(201).json(item);
});

app.listen(3000, () => console.log('CampusEats Menu on http://localhost:3000'));
