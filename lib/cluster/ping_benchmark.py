from __future__ import annotations

import socket
import time
from dataclasses import dataclass, field
from threading import Event
from typing import Callable, Literal

from ping3 import ping


ProgressCallback = Callable[[int, int, float | None], None]
PingResultStatus = Literal["ok", "unavailable", "blocked"]


@dataclass
class PingBenchmarkResult:
    host: str
    samples: list[float | None] = field(default_factory=list)
    sent: int = 0
    received: int = 0
    min_ms: float | None = None
    max_ms: float | None = None
    avg_ms: float | None = None
    loss_percent: float = 0.0
    duration_sec: float = 0.0
    jitter_ms: float | None = None
    status: PingResultStatus = "ok"


def host_resolves(host: str) -> bool:
    try:
        socket.getaddrinfo(host, None)
        return True
    except OSError:
        return False


def _compute_jitter(valid: list[float]) -> float | None:
    if len(valid) < 2:
        return None
    diffs = [abs(valid[i] - valid[i - 1]) for i in range(1, len(valid))]
    return sum(diffs) / len(diffs)


def run_ping_benchmark(
    host: str,
    *,
    count: int = 100,
    timeout: float = 1.0,
    interval: float = 0.05,
    on_progress: ProgressCallback | None = None,
    cancel_event: Event | None = None,
    blocked: bool = False,
) -> PingBenchmarkResult:
    if blocked:
        return PingBenchmarkResult(host=host, status="blocked")

    if not host_resolves(host):
        return PingBenchmarkResult(host=host, status="unavailable")

    ping.EXCEPTIONS = True
    samples: list[float | None] = []
    start = time.perf_counter()

    for index in range(count):
        if cancel_event and cancel_event.is_set():
            break

        latency: float | None = None
        try:
            delay = ping(host, timeout=timeout, unit="ms")
            if isinstance(delay, (int, float)) and delay >= 0:
                latency = float(delay)
        except Exception:
            latency = None

        samples.append(latency)
        if on_progress:
            on_progress(index + 1, count, latency)

        if index < count - 1:
            if cancel_event and cancel_event.wait(interval):
                break
            elif cancel_event is None:
                time.sleep(interval)

    duration = time.perf_counter() - start
    valid = [value for value in samples if value is not None]
    sent = len(samples)
    received = len(valid)

    return PingBenchmarkResult(
        host=host,
        samples=samples,
        sent=sent,
        received=received,
        min_ms=min(valid) if valid else None,
        max_ms=max(valid) if valid else None,
        avg_ms=(sum(valid) / len(valid)) if valid else None,
        loss_percent=((sent - received) / sent * 100.0) if sent else 0.0,
        duration_sec=duration,
        jitter_ms=_compute_jitter(valid),
    )
