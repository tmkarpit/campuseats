// Self-check for the assignment. Run: node test.js
const { spawn } = require('child_process');
const PORT = 3111, U = `http://localhost:${PORT}`;
let pass = 0, fail = 0;
const ok = (name, cond, extra = '') => { cond ? pass++ : fail++; console.log(`${cond ? 'PASS' : 'FAIL'}  ${name} ${cond ? '' : extra}`); };

let n = 0;
const call = async (method, path, body, headers = {}) => {
  headers = { 'X-Client-Id': 'c' + Math.floor(n++ / 15), ...headers }; // stay under the rate limit
  const res = await fetch(U + path, {
    method, headers: { ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...headers },
    body: body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)),
  });
  const text = await res.text();
  let json = null; try { json = JSON.parse(text); } catch {}
  return { s: res.status, h: res.headers, text, json };
};
const good = { items: [{ sku: 'widget', qty: 1 }], address: '12 Ring Road, Surat' };
const isProblem = (r, type, status) =>
  r.s === status && /^application\/problem\+json; charset=utf-8$/i.test(r.h.get('content-type')) &&
  r.json && r.json.type.endsWith('/' + type) && r.json.status === status && r.json.title && r.json.detail;

(async () => {
  const srv = spawn('node', ['server.js'], { env: { ...process.env, PORT }, stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 800));
  try {
    // A1/A3/D1 success
    let r = await call('POST', '/orders', good);
    ok('POST /orders -> 201', r.s === 201);
    ok('Location header points at new order', r.h.get('location') === `/orders/${r.json.id}`);
    ok('JSON has charset', /application\/json; charset=utf-8/.test(r.h.get('content-type')));
    const id = r.json.id;
    r = await call('GET', '/orders/' + id); ok('GET -> 200', r.s === 200);
    r = await call('PATCH', '/orders/' + id, { status: 'shipped' }); ok('PATCH -> 200', r.s === 200 && r.json.status === 'shipped');

    // A2/B1 failures
    r = await call('POST', '/orders', { items: [], address: 'x' }); ok('empty cart 422 empty-cart', isProblem(r, 'empty-cart', 422), r.text);
    r = await call('POST', '/orders', { items: [{ sku: 'widget', qty: 0 }], address: 'x' }); ok('qty 0 -> 422', isProblem(r, 'validation-failed', 422));
    r = await call('POST', '/orders', { items: [{ sku: 'widget', qty: -3 }], address: 'x' }); ok('qty -3 -> 422', r.s === 422);
    r = await call('POST', '/orders', { items: [{ sku: 'widget', qty: 1.5 }], address: 'x' }); ok('qty 1.5 -> 422', r.s === 422);
    r = await call('GET', '/orders/ord_nope'); ok('unknown id 404 order-not-found', isProblem(r, 'order-not-found', 404));
    r = await call('PATCH', '/orders/ord_nope', { status: 'shipped' }); ok('PATCH unknown 404', r.s === 404);
    r = await call('DELETE', '/orders/ord_nope'); ok('DELETE unknown 404', r.s === 404);
    r = await call('PATCH', '/orders/' + id, { status: 'paid' }); ok('illegal transition 409', isProblem(r, 'illegal-transition', 409), r.text);
    r = await call('DELETE', '/orders/' + id); ok('delete shipped order 409', isProblem(r, 'illegal-transition', 409));
    r = await call('POST', '/orders', { items: [{ sku: 'gizmo', qty: 1 }], address: 'x' }); ok('out of stock 409 item-unavailable', isProblem(r, 'item-unavailable', 409));
    r = await call('POST', '/orders', { items: [{ sku: 'nope', qty: 1 }], address: 'x' }); ok('unknown sku 409', r.s === 409);
    r = await call('POST', '/orders', { ...good, payment_token: 'tok_decline' }); ok('declined card 402', isProblem(r, 'payment-declined', 402));
    r = await call('POST', '/orders', '{bad json'); ok('malformed JSON 400', isProblem(r, 'invalid-json', 400), r.text);
    r = await call('POST', '/orders', 'hello', { 'Content-Type': 'text/plain' }); ok('wrong content-type 415', r.s === 415);
    r = await call('GET', '/nowhere'); ok('unknown route 404 problem', isProblem(r, 'route-not-found', 404));

    // B3/C2 two bad fields, all collected
    r = await call('POST', '/orders', { items: [{ sku: 'widget', qty: 0 }], address: '' });
    ok('two field errors at once', r.s === 422 && r.json.errors.length === 2 &&
       r.json.errors.some(e => e.field === 'items[0].qty') && r.json.errors.some(e => e.field === 'address'), r.text);
    r = await call('POST', '/orders', {});
    ok('missing everything -> items + address reported', r.json.errors.length === 2);

    // B4 no leaks
    r = await call('GET', '/orders/' + id, undefined, { 'X-Simulate-Fault': 'db' });
    ok('db fault -> clean 500', isProblem(r, 'internal-error', 500) && r.json.incident);
    ok('no stack / SQL text leaked', !/SQLITE|db\.js|at |node_modules/.test(r.text), r.text);

    // A4 retry-safety
    r = await call('POST', '/orders', { ...good, payment_token: 'tok_slow' }, { 'Idempotency-Key': 'slow-1' });
    ok('payment timeout 503 + Retry-After', isProblem(r, 'service-unavailable', 503) && r.h.get('retry-after') === '2');
    r = await call('POST', '/orders', good, { 'Idempotency-Key': 'slow-1' });
    ok('same key retried after 503 now succeeds (503 not cached)', r.s === 201);

    // D4 idempotency still holds
    const a = await call('POST', '/orders', good, { 'Idempotency-Key': 'k-1' });
    const b = await call('POST', '/orders', good, { 'Idempotency-Key': 'k-1' });
    ok('idempotent replay returns same order', a.s === 201 && b.s === 201 && a.json.id === b.json.id && b.h.get('idempotent-replayed') === 'true');
    const [c, d] = await Promise.all([call('POST', '/orders', good, { 'Idempotency-Key': 'k-2' }), call('POST', '/orders', good, { 'Idempotency-Key': 'k-2' })]);
    ok('concurrent same key -> one order', c.json.id === d.json.id);

    // C3 negotiation
    r = await call('GET', '/orders/' + id, undefined, { Accept: 'application/xml' });
    ok('Accept xml -> xml', r.s === 200 && /application\/xml; charset=utf-8/.test(r.h.get('content-type')) && r.text.includes(`<id>${id}</id>`), r.text);
    r = await call('GET', '/orders/' + id, undefined, { Accept: 'application/json' });
    ok('Accept json -> json', /application\/json/.test(r.h.get('content-type')));
    r = await call('GET', '/orders/' + id);
    ok('no Accept -> json default', /application\/json/.test(r.h.get('content-type')));
    r = await call('GET', '/orders/' + id, undefined, { Accept: 'text/html' });
    ok('Accept html -> 406', isProblem(r, 'not-acceptable', 406));

    // rate limit
    let last;
    for (let i = 0; i < 32; i++) last = await call('GET', '/orders', undefined, { 'X-Client-Id': 'burst' });
    ok('rate limit 429 + Retry-After', isProblem(last, 'rate-limited', 429) && Number(last.h.get('retry-after')) >= 1, last.text);

    // DELETE success
    const o = await call('POST', '/orders', good);
    r = await call('DELETE', '/orders/' + o.json.id); ok('DELETE -> 204 empty body', r.s === 204 && r.text === '');
    r = await call('GET', '/orders/' + o.json.id); ok('deleted order now 404', r.s === 404);
  } finally { srv.kill(); }
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})();
