import { randomBytes, randomUUID } from 'node:crypto';
import { next } from '@vercel/functions';

export const config = { runtime: 'nodejs' };

// Opaque formats only, not free-text names, phone numbers or credential strings.
const REQUEST_ID = /^(?:[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/;
const TRACEPARENT = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;

function randomId(bytes) {
  let id;
  do {
    id = randomBytes(bytes).toString('hex');
  } while (/^0+$/.test(id));
  return id;
}

// Runs before Vercel's static cache, so IDs belong to requests, not built pages.
export default function middleware(request) {
  const incomingId = request.headers.get('x-request-id');
  const requestId = REQUEST_ID.test(incomingId ?? '') && !/^0+$/.test(incomingId) ? incomingId : randomUUID();
  const incoming = TRACEPARENT.exec(request.headers.get('traceparent') ?? '');
  const parent = incoming && !/^0+$/.test(incoming[1]) && !/^0+$/.test(incoming[2])
    ? incoming : null;
  const traceId = parent ? parent[1] : randomId(16);
  const spanId = randomId(8);
  // Version 00 defines only the sampled bit; do not propagate reserved bits.
  const flags = parent && (parseInt(parent[3], 16) & 1) ? '01' : '00';
  const traceparent = `00-${traceId}-${spanId}-${flags}`;

  const headers = new Headers(request.headers);
  headers.set('x-request-id', requestId);
  headers.set('traceparent', traceparent);
  // No vendor-state or baggage consumers here. Do not pass opaque visitor data.
  headers.delete('tracestate');
  headers.delete('baggage');

  const response = next({
    request: { headers },
    headers: { 'x-request-id': requestId, traceparent },
  });
  // Vercel supplies URL/status metadata. Keep visitor data out of our log record.
  console.log(JSON.stringify({
    event: 'request.received',
    request_id: requestId,
    trace_id: traceId,
    span_id: spanId,
    parent_span_id: parent ? parent[2] : null,
  }));
  return response;
}
