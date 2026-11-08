"""Per-invocation synthetic metrics, never visitor telemetry or served output."""

import sys
import time

from prometheus_client import CollectorRegistry, Gauge, Histogram, write_to_textfile


class LiveMetrics:
    """One bounded registry per check; thread-safe client observations."""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.started = time.perf_counter()
        self.success = Gauge(
            "unpolitical_live_check_success",
            "Whether this check matched the production build.",
            registry=self.registry,
        )
        self.duration = Gauge(
            "unpolitical_live_check_duration_seconds",
            "Check duration including deployment waits.",
            registry=self.registry,
        )
        self.completed = Gauge(
            "unpolitical_live_check_completed_timestamp_seconds",
            "Unix completion timestamp.",
            registry=self.registry,
        )
        self.requests = Histogram(
            "unpolitical_live_http_request_duration_seconds",
            "HTTP attempt duration including body reads, excluding retry backoff.",
            ["outcome"],
            buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
            registry=self.registry,
        )
        self.sizes = Histogram(
            "unpolitical_live_http_response_size_bytes",
            "Body bytes read per HTTP attempt.",
            buckets=(0, 1024, 10_000, 50_000, 100_000, 260_000, 500_000, 1_000_000),
            registry=self.registry,
        )

    def observe(self, status, size, elapsed):
        outcome = f"{status // 100}xx" if status and 100 <= status < 600 else "network_error"
        self.requests.labels(outcome).observe(elapsed)
        self.sizes.observe(size)

    def finish(self, success, path):
        self.success.set(success)
        self.duration.set(time.perf_counter() - self.started)
        self.completed.set(time.time())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Client uses a sibling temporary file and os.replace, not partial writes.
            write_to_textfile(str(path), self.registry)
        except OSError:
            # Preserve the check's original exit/exception and previous snapshot.
            # Paths/error messages can contain credentials, so don't echo them.
            print("Warning: could not write live metrics (OSError).", file=sys.stderr)
