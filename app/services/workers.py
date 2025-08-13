"""Threaded workers for background model calls."""

from __future__ import annotations

from typing import Any, Callable

from PyQt6 import QtCore


class Worker(QtCore.QThread):
    """Generic worker executing a callable in a ``QThread``."""

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception)

    def __init__(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:  # type: ignore[override]
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as exc:  # pragma: no cover - network/IO safety
            self.error.emit(exc)
        else:
            self.finished.emit(result)


class ModelWorker(Worker):
    """Worker executing ``model.translate`` in the background."""

    def __init__(self, model: Any, text: str, **kwargs: Any) -> None:
        super().__init__(model.translate, text, **kwargs)
