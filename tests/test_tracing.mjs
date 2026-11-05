import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import middleware, { config } from '../middleware.js';

const TRACE_ID = '4bf92f3577b34da6a3ce929d0e0e4736';
const PARENT_ID = '00f067aa0ba902b7';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const TRACEPARENT = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;

function invoke(t, headers = {}, path = '/', method = 'GET') {
  const log = t.mock.method(console, 'log', () => {});
  const request = new Request(`https://example.test${path}`, { headers, method });
  const before = [...request.headers];
  const response = middleware(request);
  assert.deepEqual([...request.headers], before, 'do not mutate the incoming request');
  assert.equal(log.mock.callCount(), 1);
  const record = JSON.parse(log.mock.calls[0].arguments[0]);
  log.mock.restore();
  return { response, record };
}

function checkContext(response, record) {
  const requestId = response.headers.get('x-request-id');
  const traceparent = response.headers.get('traceparent');
  const match = TRACEPARENT.exec(traceparent);
  assert.ok(match, 'emit a valid version-00 traceparent');
  assert.notEqual(match[1], '0'.repeat(32));
  assert.notEqual(match[2], '0'.repeat(16));
  assert.equal(record.event, 'request.received');
  assert.equal(record.request_id, requestId);
  assert.equal(record.trace_id, match[1]);
  assert.equal(record.span_id, match[2]);
  // Inspect the real @vercel/functions continuation, not a mocked helper.
  assert.equal(response.headers.get('x-middleware-next'), '1');
  assert.equal(response.headers.get('x-middleware-request-x-request-id'), requestId);
  assert.equal(response.headers.get('x-middleware-request-traceparent'), traceparent);
  const forwarded = response.headers.get('x-middleware-override-headers').split(',');
  assert.ok(forwarded.includes('x-request-id'));
  assert.ok(forwarded.includes('traceparent'));
  assert.equal(response.body, null, 'let Vercel serve the static body and status');
  assert.equal(response.headers.has('cache-control'), false);
  assert.equal(response.headers.has('set-cookie'), false);
  return match;
}

test('new requests get independent IDs in logs, response and downstream headers', (t) => {
  const first = invoke(t);
  const second = invoke(t);
  checkContext(first.response, first.record);
  checkContext(second.response, second.record);
  assert.match(first.record.request_id, UUID);
  assert.equal(first.record.parent_span_id, null);
  assert.equal(first.response.headers.get('traceparent').slice(-2), '00');
  for (const field of ['request_id', 'trace_id', 'span_id']) {
    assert.notEqual(first.record[field], second.record[field]);
  }
});

for (const requestId of ['proxy-123_abc.example', 'A', 'a'.repeat(128)]) {
  test(`preserves a safe request ID (${requestId.length} characters)`, (t) => {
    const { response, record } = invoke(t, { 'X-Request-ID': requestId });
    checkContext(response, record);
    assert.equal(record.request_id, requestId);
  });
}

for (const requestId of ['', 'a'.repeat(129), 'first, second', 'space inside', 'bad/value']) {
  test(`replaces an invalid request ID (${requestId.slice(0, 20)})`, (t) => {
    const { response, record } = invoke(t, { 'x-request-id': requestId });
    checkContext(response, record);
    assert.match(record.request_id, UUID);
  });
}

for (const flags of ['00', '01']) {
  test(`continues the caller trace and records the parent (flags ${flags})`, (t) => {
    const { response, record } = invoke(t, {
      'x-request-id': 'caller-123',
      traceparent: `00-${TRACE_ID}-${PARENT_ID}-${flags}`,
    });
    const match = checkContext(response, record);
    assert.equal(record.request_id, 'caller-123');
    assert.equal(record.trace_id, TRACE_ID);
    assert.equal(record.parent_span_id, PARENT_ID);
    assert.notEqual(record.span_id, PARENT_ID);
    assert.equal(match[3], flags);
  });
}

const invalidParents = [
  '',
  'not-a-trace',
  `00-${'0'.repeat(32)}-${PARENT_ID}-01`,
  `00-${TRACE_ID}-${'0'.repeat(16)}-01`,
  `00-${TRACE_ID.toUpperCase()}-${PARENT_ID}-01`,
  `ff-${TRACE_ID}-${PARENT_ID}-01`,
  `00-${TRACE_ID}-${PARENT_ID}-zz`,
  `00-${TRACE_ID}-${PARENT_ID}-01-extra`,
  `00-${TRACE_ID}-${PARENT_ID}-01,00-${TRACE_ID}-${PARENT_ID}-01`,
];
for (const [index, traceparent] of invalidParents.entries()) {
  test(`starts a clean trace for malformed context ${index + 1}`, (t) => {
    const { response, record } = invoke(t, {
      traceparent, tracestate: 'vendor=opaque', baggage: 'visitor=private',
    });
    const match = checkContext(response, record);
    assert.notEqual(record.trace_id, TRACE_ID);
    assert.equal(record.parent_span_id, null);
    assert.equal(match[3], '00');
    assert.equal(response.headers.has('x-middleware-request-tracestate'), false);
    assert.equal(response.headers.has('x-middleware-request-baggage'), false);
  });
}

test('sibling requests keep their trace but use different spans', (t) => {
  const headers = { traceparent: `00-${TRACE_ID}-${PARENT_ID}-01` };
  const first = invoke(t, headers);
  const second = invoke(t, headers);
  assert.equal(first.record.trace_id, second.record.trace_id);
  assert.notEqual(first.record.span_id, second.record.span_id);
});

test('logs only correlation fields and does not expose other headers', (t) => {
  const { response, record } = invoke(t, {
    authorization: 'Bearer private-test-value',
    cookie: 'session=private-test-cookie',
    tracestate: 'vendor=private-test-state',
    baggage: 'email=private-test-baggage',
    traceparent: `00-${TRACE_ID}-${PARENT_ID}-01`,
  }, '/private-test-path?email=private-test-query');
  checkContext(response, record);
  assert.deepEqual(Object.keys(record).sort(), [
    'event', 'parent_span_id', 'request_id', 'span_id', 'trace_id',
  ]);
  assert.ok(!JSON.stringify(record).includes('private-test'));
  for (const name of ['authorization', 'cookie', 'tracestate', 'baggage']) {
    assert.equal(response.headers.has(name), false);
  }
  for (const name of ['tracestate', 'baggage']) {
    assert.equal(response.headers.has(`x-middleware-request-${name}`), false);
  }
  assert.equal(response.headers.get('x-middleware-request-authorization'), 'Bearer private-test-value');
  assert.equal(response.headers.get('x-middleware-request-cookie'), 'session=private-test-cookie');
});

for (const [path, method] of [
  ['/', 'GET'], ['/life/2020.html', 'HEAD'], ['/data/facts.json', 'GET'],
  ['/style.css', 'GET'], ['/not-found.html', 'GET'],
]) {
  test(`continues ${method} ${path} without replacing static content`, (t) => {
    const { response, record } = invoke(t, {}, path, method);
    checkContext(response, record);
  });
}

test('Vercel enables the middleware for all paths and installs its locked helper', async () => {
  const root = new URL('../', import.meta.url);
  const vercel = JSON.parse(await readFile(new URL('vercel.json', root)));
  const pkg = JSON.parse(await readFile(new URL('package.json', root)));
  const lock = JSON.parse(await readFile(new URL('package-lock.json', root)));
  assert.equal(vercel.proxy.entrypoint, 'middleware.js');
  assert.equal(vercel.proxy.matcher, undefined);
  assert.equal(config.matcher, undefined);
  assert.equal(config.runtime, 'nodejs');
  assert.equal(vercel.installCommand, 'npm ci --ignore-scripts && make setup');
  assert.equal(vercel.buildCommand, 'make build');
  assert.equal(vercel.outputDirectory, 'site');
  assert.equal(pkg.type, 'module');
  assert.equal(lock.packages['node_modules/@vercel/functions'].version, pkg.dependencies['@vercel/functions']);
});
