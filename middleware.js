import { randomBytes, randomUUID } from 'node:crypto';
import { next } from '@vercel/functions';

export const config = { runtime: 'nodejs' };

const REQUEST_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
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
  const requestId = REQUEST_ID.test(incomingId ?? '') ? incomingId : randomUUID();
  const incoming = TRACEPARENT.exec(request.headers.get('traceparent') ?? '');
  const parent = incoming && !/^0+$/.test(incoming[1]) && !/^0+$/.test(incoming[2])
    ? incoming : null;
  const traceId = parent ? parent[1] : randomId(16);
  const spanId = randomId(8);
  const traceparent = `00-${traceId}-${spanId}-${parent ? parent[3] : '00'}`;

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
