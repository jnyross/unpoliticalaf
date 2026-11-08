import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import middleware, { config } from '../middleware.js';

const TRACE_ID = '4bf92f3577b34da6a3ce929d0e0e4736';
const PARENT_ID = '00f067aa0ba902b7';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const TRACEPARENT = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;

test('real SDK and middleware import without logging, network, process or file writes', () => {
  const result = spawnSync(process.execPath, ['--input-type=module', '--eval', `
    import assert from 'node:assert/strict';
    import childProcess from 'node:child_process';
    import dns from 'node:dns';
    import fs from 'node:fs';
    import http from 'node:http';
    import https from 'node:https';
    import net from 'node:net';
    import { syncBuiltinESMExports } from 'node:module';
    const deny = () => { throw new Error('Unexpected import side effect'); };
    for (const name of ['spawn', 'spawnSync', 'exec', 'execSync', 'execFile', 'execFileSync', 'fork']) {
      childProcess[name] = deny;
    }
    for (const client of [http, https]) {
      client.request = deny;
      client.get = deny;
    }
    net.Socket.prototype.connect = deny;
    dns.lookup = deny;
    globalThis.fetch = deny;
    for (const name of ['writeFile', 'appendFile', 'mkdir', 'unlink', 'rename']) {
      fs[name] = deny;
      fs[name + 'Sync'] = deny;
      fs.promises[name] = deny;
    }
    for (const name of ['log', 'warn', 'error', 'info', 'debug']) console[name] = deny;
    syncBuiltinESMExports();
    const module = await import(${JSON.stringify(new URL('../middleware.js', import.meta.url).href)});
    assert.equal(typeof module.default, 'function');
  `], { env: {}, encoding: 'utf8', timeout: 10000 });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, '');
});

function invoke(t, headers = {}, path = '/', method = 'GET', body) {
  const log = t.mock.method(console, 'log', () => {});
  const request = new Request(`https://example.test${path}`, { headers, method, body });
  const before = [...request.headers];
  let response;
  try {
    response = middleware(request);
  } finally {
    log.mock.restore();
  }
  assert.deepEqual([...request.headers], before, 'do not mutate the incoming request');
  assert.equal(log.mock.callCount(), 1);
  const record = JSON.parse(log.mock.calls[0].arguments[0]);
  return { response, record, request };
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
  assert.equal(response.headers.has('vary'), false);
  assert.equal(response.headers.has('location'), false);
  assert.equal(response.headers.has('x-middleware-rewrite'), false);
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

for (const requestId of ['c6277c8e-8b98-4f9a-81c8-a50bbecb57dd', TRACE_ID]) {
  test(`preserves a safe request ID (${requestId.length} characters)`, (t) => {
    const { response, record } = invoke(t, { 'X-Request-ID': requestId });
    checkContext(response, record);
    assert.equal(record.request_id, requestId);
  });
}

test('duplicate request and trace headers reset instead of selecting a caller value', (t) => {
  const headers = new Headers();
  for (let i = 0; i < 2; i += 1) {
    headers.append('x-request-id', TRACE_ID);
    headers.append('traceparent', `00-${TRACE_ID}-${PARENT_ID}-01`);
  }
  const { response, record } = invoke(t, headers);
  checkContext(response, record);
  assert.match(record.request_id, UUID);
  assert.notEqual(record.trace_id, TRACE_ID);
  assert.equal(record.parent_span_id, null);
});

test('unsafe correlation inputs cannot smuggle synthetic visitor data into logs', (t) => {
  const { response, record } = invoke(t, {
    'x-request-id': 'synthetic-private-name',
    traceparent: 'synthetic-private-token',
    'user-agent': 'synthetic-private-agent',
    referer: 'https://example.test/synthetic-private-referrer',
    'x-forwarded-for': '192.0.2.42',
  });
  checkContext(response, record);
  assert.ok(!JSON.stringify(record).includes('synthetic-private'));
  assert.ok(!JSON.stringify(record).includes('192.0.2.42'));
  assert.deepEqual(Object.keys(record).sort(), [
    'event', 'parent_span_id', 'request_id', 'span_id', 'trace_id',
  ]);
});

test('does not read or consume a request body or change cache and conditional inputs', async (t) => {
  const headers = {
    'cache-control': 'no-cache',
    'if-none-match': '"synthetic-etag"',
    'if-modified-since': 'Fri, 06 Nov 2026 00:00:00 GMT',
    range: 'bytes=0-10',
  };
  const { response, record, request } = invoke(t, headers, '/', 'POST', 'synthetic-private-body');
  checkContext(response, record);
  assert.equal(request.method, 'POST');
  assert.equal(request.url, 'https://example.test/');
  assert.equal(request.bodyUsed, false);
  assert.equal(await request.text(), 'synthetic-private-body');
  assert.ok(!JSON.stringify(record).includes('synthetic-private-body'));
  for (const [name, value] of Object.entries(headers)) {
    assert.equal(response.headers.get(`x-middleware-request-${name}`), value);
  }
});

for (const requestId of ['', 'a'.repeat(129), 'first, second', 'space inside', 'bad/value', 'A',
  'john.smith', '07700900123', 'a'.repeat(31), 'a'.repeat(33), '0'.repeat(32),
  TRACE_ID.toUpperCase()]) {
  test(`replaces an invalid request ID (${requestId.slice(0, 20)})`, (t) => {
    const { response, record } = invoke(t, { 'x-request-id': requestId });
    checkContext(response, record);
    assert.match(record.request_id, UUID);
  });
}

for (const flags of ['00', '01', '02', 'fe', 'ff']) {
  test(`continues the caller trace and records the parent (flags ${flags})`, (t) => {
    const { response, record } = invoke(t, {
      'x-request-id': TRACE_ID,
      traceparent: `00-${TRACE_ID}-${PARENT_ID}-${flags}`,
    });
    const match = checkContext(response, record);
    assert.equal(record.request_id, TRACE_ID);
    assert.equal(record.trace_id, TRACE_ID);
    assert.equal(record.parent_span_id, PARENT_ID);
    assert.notEqual(record.span_id, PARENT_ID);
    assert.equal(match[3], (parseInt(flags, 16) & 1).toString(16).padStart(2, '0'));
  });
}

const invalidParents = [
  '',
  'not-a-trace',
  `00-${'0'.repeat(32)}-${PARENT_ID}-01`,
  `00-${TRACE_ID}-${'0'.repeat(16)}-01`,
  `00-${TRACE_ID.toUpperCase()}-${PARENT_ID}-01`,
  `ff-${TRACE_ID}-${PARENT_ID}-01`,
  `01-${TRACE_ID}-${PARENT_ID}-01`,
  `00-${TRACE_ID}-${PARENT_ID}-1`,
  `00-${TRACE_ID.slice(1)}-${PARENT_ID}-01`,
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
  assert.equal(vercel.installCommand, 'npm ci --ignore-scripts --omit=dev && make setup');
  assert.equal(vercel.buildCommand, 'make production-build');
  assert.equal(vercel.outputDirectory, 'site');
  assert.equal(pkg.type, 'module');
  assert.equal(pkg.engines.node, '22.x');
  assert.deepEqual(vercel.git.deploymentEnabled, { main: true, '*': false, '**': false });
  assert.equal(pkg.devDependencies.jscpd, '4.0.5');
  assert.equal(lock.packages['node_modules/jscpd'].version, '4.0.5');
  assert.equal(pkg.dependencies['@vercel/functions'], '3.10.6');
  assert.equal(lock.packages['node_modules/@vercel/functions'].version, pkg.dependencies['@vercel/functions']);
});
