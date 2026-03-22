"""OpenTelemetry trace context helpers for Copilot SDK.

Note: OpenTelemetry imports are disabled in this vendored copy to prevent
blocking I/O inside the Home Assistant asyncio event loop. Tracing is not
used by the HA integration, so these functions are safe to stub out.
"""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator


def get_trace_context() -> dict[str, str]:
    """Return empty trace context (OpenTelemetry disabled in HA integration)."""
    return {}


@contextmanager
def trace_context(traceparent: str | None, tracestate: str | None) -> Generator[None, None, None]:
    """No-op context manager (OpenTelemetry disabled in HA integration)."""
    yield
