"""Threaded workers for background model calls."""

from __future__ import annotations

from typing import Any, Callable

import threading
import time

from PyQt6 import QtCore


class RateLimiter:
    """Simple thread-safe rate limiter."""

    def __init__(self, rps: float) -> None:
        self.interval = 1.0 / rps if rps > 0 else 0.0
        self.lock = threading.Lock()
        self.last_call = 0.0

    def wait(self) -> None:
        """Block until the next call is allowed."""

        with self.lock:
            now = time.perf_counter()
            delay = self.last_call + self.interval - now
            if delay > 0:
                time.sleep(delay)
            self.last_call = time.perf_counter()


class Worker(QtCore.QThread):
    """Generic worker executing a callable in a ``QThread``."""

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception)

    def __init__(
        self,
        func: Callable[..., Any],
        *args: Any,
        rate_limiter: RateLimiter | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.rate_limiter = rate_limiter

    def run(self) -> None:  # type: ignore[override]
        try:
            if self.rate_limiter is not None:
                self.rate_limiter.wait()
            result = self.func(*self.args, **self.kwargs)
        except Exception as exc:  # pragma: no cover - network/IO safety
            self.error.emit(exc)
        else:
            self.finished.emit(result)


class ModelWorker(Worker):
    """Worker executing ``model.translate`` in the background."""

    def __init__(
        self,
        model: Any,
        text: str,
        rate_limiter: RateLimiter | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model.translate, text, rate_limiter=rate_limiter, **kwargs)


# Default limiter allowing one request per second
DEFAULT_RATE_LIMITER = RateLimiter(1.0)
