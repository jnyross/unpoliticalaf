# Live-site performance metrics

This application is a static site, not a long-running Python web server.
`scripts/check_live.py` uses the Prometheus Python client to measure its existing
synthetic HTTP checks. It adds no requests, browser tracking, external telemetry
service, credentials or paid integration.

## Collection

`make live` builds and checks the live site, then atomically writes
`.metrics/live.prom`, even when the live check fails. The existing daily and
post-push `Live site matches main` workflow retains the file as the
`live-site-metrics` artifact for 14 days, including failures. No new schedule is
introduced. Download artifacts from successive runs to investigate regressions.

After `make setup && make build`, choose a different destination if needed:

```sh
.venv/bin/python scripts/check_live.py --metrics-file /var/lib/node_exporter/textfile_collector/unpolitical_live.prom
```

On a machine already running Prometheus Node Exporter, configure its
`--collector.textfile.directory` to that directory and grant the check's user
write access. Prometheus scrapes Node Exporter, not the static website. This PR
does not provision a collector or activate an external service. CI artifacts are
available without one. Keep the file outside `site/`; the CLI rejects a
destination inside the build so telemetry cannot change the public build hashes.
Local `.metrics/` output is ignored by Git.

## Measurements

| Metric | Meaning |
| --- | --- |
| `unpolitical_live_check_success` | 1 only if commit, manifest and every served file match; otherwise 0 |
| `unpolitical_live_check_duration_seconds` | Whole check, including retries and deployment waits, excluding the local build |
| `unpolitical_live_check_completed_timestamp_seconds` | Check completion Unix time, to detect stale results |
| `unpolitical_live_http_request_duration_seconds` | Histogram of each HTTP attempt, through reading its body |
| `unpolitical_live_http_response_size_bytes` | Histogram of response body bytes actually read per attempt |

Request durations have a bounded `outcome` label (`1xx` through `5xx`, or
`network_error`). Retries are measured individually; backoff and deployment
waiting are excluded from HTTP latency. HTTP error bodies are not read, so their
recorded response size is zero. Network error messages are not counted as bytes.
Requests run concurrently, so summed request durations can exceed wall time.
No URLs, query strings, page paths, exception messages, commit hashes, visitor
identifiers or credentials are exported as metric labels.

Each file is a **snapshot of one run**. Histograms reset on each invocation:
use their buckets, count and sum directly, not `rate()` or `increase()`. For
example, with an existing Prometheus collector:

```promql
# Average successful HTTP attempt time in the latest check
unpolitical_live_http_request_duration_seconds_sum{outcome="2xx"}
/
unpolitical_live_http_request_duration_seconds_count{outcome="2xx"}

# Approximate p95 across successful requests in the latest check
histogram_quantile(0.95, unpolitical_live_http_request_duration_seconds_bucket{outcome="2xx"})

# Latest check failed
unpolitical_live_check_success == 0

# No completed check for more than 26 hours (for the daily workflow)
time() - unpolitical_live_check_completed_timestamp_seconds > 26 * 3600
```

Also alert on an absent completion metric if a collector is configured. Missing
HTTP series mean no such attempt was observed, not that its latency was zero.
An unwritable metrics destination emits a warning without changing the original
check result or masking an exception. Atomic replacement leaves the previous
snapshot intact on write failure; use its completion time to detect staleness.

These are synthetic observations from the checker, not real-user Core Web
Vitals, Vercel request traffic or continuous uptime measurements. Deployment
waits affect overall check time, not request latency. No claim of production
collection is made until the workflow runs or an operator configures a collector.
