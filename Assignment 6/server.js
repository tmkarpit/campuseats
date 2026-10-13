// CS543 A06 - Orders service (builds on A5: idempotency + payment timeout kept)
const express = require('express');
const crypto = require('crypto');

const app = express();
app.disable('x-powered-by');

// ---------------------------------------------------------------- catalogue
const BASE = 'https://cs543.example/problems/';
const TYPES = {
  'invalid-json':       { status: 400, title: 'Malformed JSON body' },
  'validation-failed':  { status: 422, title: 'Request validation failed' },
  'empty-cart':         { status: 422, title: 'Cart is empty' },
  'item-unavailable':   { status: 409, title: 'Item unavailable' },
  'payment-declined':   { status: 402, title: 'Payment declined' },
  'order-not-found':    { status: 404, title: 'Order not found' },
  'illegal-transition': { status: 409, title: 'Illegal status transition' },
  'not-acceptable':     { status: 406, title: 'Representation not available' },
  'unsupported-media':  { status: 415, title: 'Unsupported media type' },
  'rate-limited':       { status: 429, title: 'Too many requests' },
  'service-unavailable':{ status: 503, title: 'Payment service unavailable' },
  'route-not-found':    { status: 404, title: 'Route not found' },
  'internal-error':     { status: 500, title: 'Internal server error' },
};

// problem() builds a result object; reply() is the only thing that writes to the socket.
function problem(key, detail, extra = {}, headers = {}) {
  const t = TYPES[key];
  return { status: t.status, isProblem: true, headers,
           data: { type: BASE + key, title: t.title, status: t.status, detail, ...extra } };
}

// ---------------------------------------------------------------- data
const STOCK = { widget: 10, gadget: 5, gizmo: 0 };
const PRICE_CENTS = { widget: 999, gadget: 2450, gizmo: 10000 };
const orders = new Map();
let nextId = 1001;
const idem = new Map(); // Idempotency-Key -> Promise<result>

const NEXT = { paid: ['shipped', 'cancelled'], shipped: ['delivered'], delivered: [], cancelled: [] };

// ---------------------------------------------------------------- helpers
const esc = s => String(s).replace(/[<>&"']/g,
  c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[c]));
function xml(name, v) {
  if (Array.isArray(v)) {
    const one = name.replace(/s$/, '');
    return `<${name}>${v.map(x => xml(one, x)).join('')}</${name}>`;
  }
  if (v && typeof v === 'object')
    return `<${name}>${Object.entries(v).map(([k, x]) => xml(k, x)).join('')}</${name}>`;
  return `<${name}>${esc(v)}</${name}>`;
}

function reply(res, r) {
  res.status(r.status);
  for (const [k, v] of Object.entries(r.headers || {})) res.set(k, v);
  if (r.data === undefined) return res.end();
  if (r.isProblem) {                                  // errors are always problem+json
    res.set('Content-Type', 'application/problem+json; charset=utf-8');
    return res.send(JSON.stringify(r.data));
  }
  if (res.locals.format === 'xml') {
    res.set('Content-Type', 'application/xml; charset=utf-8');
    return res.send('<?xml version="1.0" encoding="UTF-8"?>' + xml(r.root, r.data));
  }
  res.set('Content-Type', 'application/json; charset=utf-8');
  return res.send(JSON.stringify(r.data));
}

// wrap handlers: anything thrown becomes a clean 500, details only go to the log
const handle = fn => async (req, res) => {
  let r;
  try { r = await fn(req, res); }
  catch (err) {
    const incident = crypto.randomBytes(4).toString('hex');
    console.error(`[incident ${incident}]`, err.stack || err);
    r = problem('internal-error', 'Something went wrong on our side. Quote the incident id if you contact support.', { incident });
  }
  reply(res, r);
};

// fake database layer, so we have something risky to wrap
function dbRead(id, fault) {
  if (fault === 'db') throw new Error('SQLITE_ERROR: no such table: orders_v2 at /srv/app/db.js:42');
  return orders.get(id);
}

// ---------------------------------------------------------------- middleware
// 1. rate limit: 30 requests / 10 s per client (X-Client-Id header or IP)
const hits = new Map();
app.use((req, res, next) => {
  res.locals.format = 'json';
  const who = req.get('X-Client-Id') || req.ip, now = Date.now();
  const recent = (hits.get(who) || []).filter(t => now - t < 10000);
  if (recent.length >= 30) {
    const wait = Math.max(1, Math.ceil((recent[0] + 10000 - now) / 1000));
    return reply(res, problem('rate-limited', `Limit is 30 requests per 10 seconds. Retry in ${wait}s.`, {}, { 'Retry-After': String(wait) }));
  }
  recent.push(now); hits.set(who, recent); next();
});

// 2. content negotiation: json (default) or xml, else 406
app.use((req, res, next) => {
  const accept = req.get('Accept');
  const f = req.accepts(['json', 'xml']);
  if (accept && !f && !req.accepts('application/problem+json'))
    return reply(res, problem('not-acceptable', `Cannot produce '${accept}'. Supported: application/json, application/xml.`));
  res.locals.format = f === 'xml' ? 'xml' : 'json';
  next();
});

// 3. body must be JSON when present
app.use((req, res, next) => {
  const hasBody = req.get('Content-Length') > 0 || req.get('Transfer-Encoding');
  if (hasBody && !req.is('application/json'))
    return reply(res, problem('unsupported-media', 'Send the body as application/json.'));
  next();
});
app.use(express.json());

// ---------------------------------------------------------------- validation
function validateNewOrder(b) {
  const errors = [];
  let empty = false;
  if (typeof b !== 'object' || b === null || Array.isArray(b))
    return problem('validation-failed', 'Body must be a JSON object.', { errors: [{ field: 'body', message: 'must be a JSON object' }] });

  if (!Array.isArray(b.items)) errors.push({ field: 'items', message: 'is required and must be an array' });
  else if (b.items.length === 0) { empty = true; errors.push({ field: 'items', message: 'must contain at least one item' }); }
  else b.items.forEach((it, i) => {
    if (typeof it !== 'object' || it === null) return errors.push({ field: `items[${i}]`, message: 'must be an object' });
    if (typeof it.sku !== 'string' || !it.sku.trim()) errors.push({ field: `items[${i}].sku`, message: 'is required and must be a non-empty string' });
    if (!Number.isInteger(it.qty) || it.qty < 1) errors.push({ field: `items[${i}].qty`, message: 'must be an integer >= 1' });
  });
  if (typeof b.address !== 'string' || !b.address.trim()) errors.push({ field: 'address', message: 'is required and must be a non-empty string' });
  if (b.payment_token !== undefined && typeof b.payment_token !== 'string')
    errors.push({ field: 'payment_token', message: 'must be a string when supplied' });

  if (!errors.length) return null;
  return empty
    ? problem('empty-cart', 'The cart has no items.', { errors })
    : problem('validation-failed', `${errors.length} field(s) failed validation.`, { errors });
}

// ---------------------------------------------------------------- payment (A5 timeout kept)
function charge(token) {
  return new Promise((resolve, reject) => {
    const guard = setTimeout(() => reject(new Error('PAYMENT_TIMEOUT')), 1000);
    setTimeout(() => { clearTimeout(guard); resolve({ ok: token !== 'tok_decline' }); }, token === 'tok_slow' ? 3000 : 50);
  });
}

// ---------------------------------------------------------------- create order
async function createOrder(body) {
  const bad = validateNewOrder(body);
  if (bad) return bad;

  const wanted = {};
  body.items.forEach(i => { wanted[i.sku] = (wanted[i.sku] || 0) + i.qty; });
  const unavailable = [];
  for (const [sku, qty] of Object.entries(wanted)) {
    if (!(sku in STOCK)) unavailable.push({ sku, reason: 'unknown sku' });
    else if (STOCK[sku] < qty) unavailable.push({ sku, reason: `only ${STOCK[sku]} in stock, ${qty} requested` });
  }
  if (unavailable.length) return problem('item-unavailable', 'One or more items cannot be fulfilled.', { unavailable });

  for (const [sku, qty] of Object.entries(wanted)) STOCK[sku] -= qty;   // reserve
  const release = () => { for (const [sku, qty] of Object.entries(wanted)) STOCK[sku] += qty; };

  let paid;
  try { paid = await charge(body.payment_token || 'tok_ok'); }
  catch (e) {
    release();
    if (e.message === 'PAYMENT_TIMEOUT')
      return problem('service-unavailable', 'The payment provider did not answer in time. Nothing was charged; retry shortly.', {}, { 'Retry-After': '2' });
    throw e;
  }
  if (!paid.ok) { release(); return problem('payment-declined', 'The payment provider declined the card.'); }

  const id = 'ord_' + nextId++;
  const items = body.items.map(i => ({ sku: i.sku, qty: i.qty, unit_price: PRICE_CENTS[i.sku] / 100 }));
  const cents = body.items.reduce((s, i) => s + PRICE_CENTS[i.sku] * i.qty, 0);
  const order = { id, status: 'paid', items, address: body.address.trim(), total: cents / 100, created_at: new Date().toISOString() };
  orders.set(id, order);
  return { status: 201, headers: { Location: `/orders/${id}` }, data: order, root: 'order' };
}

// ---------------------------------------------------------------- routes
app.post('/orders', handle(async (req) => {
  const key = req.get('Idempotency-Key');
  if (!key) return createOrder(req.body);

  if (idem.has(key)) {
    const r = await idem.get(key);
    return { ...r, headers: { ...r.headers, 'Idempotent-Replayed': 'true' } };
  }
  const p = createOrder(req.body);
  idem.set(key, p);
  try {
    const r = await p;
    if (r.status >= 500 || r.status === 429) idem.delete(key);  // transient: allow a real retry
    return r;
  } catch (e) { idem.delete(key); throw e; }
}));

app.get('/orders', handle(async () => ({
  status: 200, root: 'orders', data: [...orders.values()],
})));

const notFound = id => problem('order-not-found', `No order with id '${id}'.`);

app.get('/orders/:id', handle(async (req) => {
  const o = dbRead(req.params.id, req.get('X-Simulate-Fault'));
  return o ? { status: 200, data: o, root: 'order' } : notFound(req.params.id);
}));

app.patch('/orders/:id', handle(async (req) => {
  const o = orders.get(req.params.id);
  if (!o) return notFound(req.params.id);

  const b = req.body, errors = [];
  if (typeof b !== 'object' || b === null || Array.isArray(b))
    return problem('validation-failed', 'Body must be a JSON object.', { errors: [{ field: 'body', message: 'must be a JSON object' }] });
  if (b.status === undefined && b.address === undefined) errors.push({ field: 'body', message: "send at least one of 'status' or 'address'" });
  if (b.status !== undefined && !(b.status in NEXT)) errors.push({ field: 'status', message: `must be one of: ${Object.keys(NEXT).join(', ')}` });
  if (b.address !== undefined && (typeof b.address !== 'string' || !b.address.trim())) errors.push({ field: 'address', message: 'must be a non-empty string' });
  if (errors.length) return problem('validation-failed', `${errors.length} field(s) failed validation.`, { errors });

  if (b.status !== undefined && b.status !== o.status) {
    if (!NEXT[o.status].includes(b.status))
      return problem('illegal-transition', `Cannot move an order from '${o.status}' to '${b.status}'.`, { allowed: NEXT[o.status] });
    if (b.status === 'cancelled') o.items.forEach(i => { STOCK[i.sku] += i.qty; });
    o.status = b.status;
  }
  if (b.address !== undefined) o.address = b.address.trim();
  return { status: 200, data: o, root: 'order' };
}));

app.delete('/orders/:id', handle(async (req) => {
  const o = orders.get(req.params.id);
  if (!o) return notFound(req.params.id);
  if (o.status === 'shipped' || o.status === 'delivered')
    return problem('illegal-transition', `Cannot delete an order that is '${o.status}'.`, { allowed: [] });
  if (o.status === 'paid') o.items.forEach(i => { STOCK[i.sku] += i.qty; });
  orders.delete(o.id);
  return { status: 204 };
}));

// ---------------------------------------------------------------- fallbacks
app.use((req, res) => reply(res, problem('route-not-found', `${req.method} ${req.path} does not exist.`)));

// body-parser and anything else that escapes the handlers
app.use((err, req, res, next) => {
  if (err.type === 'entity.parse.failed')
    return reply(res, problem('invalid-json', 'The request body is not valid JSON.'));
  const incident = crypto.randomBytes(4).toString('hex');
  console.error(`[incident ${incident}]`, err.stack || err);
  reply(res, problem('internal-error', 'Something went wrong on our side.', { incident }));
});

const PORT = process.env.PORT || 3000;
if (require.main === module) app.listen(PORT, () => console.log(`Orders service on :${PORT}`));
module.exports = app;
