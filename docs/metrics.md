# Synthetic live-check metrics

`make live` uses the production configuration and the virtualenv interpreter.
Each invocation exports `.metrics/live.prom` outside `site/`, even on failed
verification or an unexpected exception. `--metrics-file /path/live.prom` selects
another destination, never within the public site (including through symlinks).
No metrics are added to generated pages.

The pinned `prometheus-client==0.26.0` is a checker runtime dependency, installed
by the canonical `make setup` so every live/deploy entry point can import it.
There is no server, browser tracking, visitor data, additional service or backend.

| Metric | Meaning |
| --- | --- |
| `unpolitical_live_check_success` | This invocation matched the production build |
| `unpolitical_live_check_duration_seconds` | Total duration including deployment waits |
| `unpolitical_live_check_completed_timestamp_seconds` | Completion time, not deployment time |
| `unpolitical_live_http_request_duration_seconds` | Histogram per HTTP attempt, body reads included, retry backoff excluded |
| `unpolitical_live_http_response_size_bytes` | Histogram of bytes actually read per attempt |

The only label is bounded `outcome`: `1xx` through `5xx`, or `network_error`.
No URL, path, query, error message, visitor, commit or request ID becomes a label.
HTTP errors close their response without reading its body, so their measured size
is zero. Network errors retry up to three attempts; HTTP errors do not retry.

Every check creates a fresh registry. Counters/histograms describe one invocation,
not a continuous process, so do not apply `rate()` across successive snapshots.
The client atomically replaces the textfile with a sibling temporary file.
Export I/O failure warns without changing the original check exit or exception;
the prior snapshot may remain. Always check completion time for staleness.

The canonical `deploy.yml` retains live and receipt-check snapshots separately,
with `if: always()`, run/attempt-specific artifact names and 14-day retention.
Receipt, site release and version-notes writers require
`REVIEWED_PRODUCTION_DELIVERY` to equal `true`; this integration does not set
it. Legacy `live.yml` delegates instead of duplicating checks. No daily schedule
is activated.

An existing Node Exporter textfile collector can read an operator-selected path.
That optional configuration is not performed here. Example PromQL:

```promql
unpolitical_live_check_success == 0
time() - unpolitical_live_check_completed_timestamp_seconds > 90000
histogram_quantile(0.95, sum by (le) (unpolitical_live_http_request_duration_seconds_bucket))
```

These are synthetic availability/latency observations, not real-user performance,
production collection history, a deployment receipt or a shipping-cadence claim.
