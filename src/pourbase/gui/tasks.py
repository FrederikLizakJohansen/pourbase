"""Background work on a thread pool with per-kind cancellation."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from ..exceptions import CalculationCancelled


class _Signals(QObject):
    finished = Signal(str, object, object, str)
    progress = Signal(str, object, float)


class _Task(QRunnable):
    def __init__(self, kind: str, key: Any, work: Callable, signals: _Signals, cancel: threading.Event) -> None:
        super().__init__()
        self.kind, self.key, self.work, self.signals, self.cancel = kind, key, work, signals, cancel

    def run(self) -> None:
        def progress(fraction: float) -> bool:
            self._emit(self.signals.progress, fraction)
            return not self.cancel.is_set()

        try:
            result = self.work(progress)
        except CalculationCancelled:
            self._emit(self.signals.finished, None, "")
        except Exception as error:
            self._emit(self.signals.finished, None, f"{type(error).__name__}: {error}")
        else:
            self._emit(self.signals.finished, result, "")

    def _emit(self, signal: Any, *arguments: Any) -> None:
        try:
            signal.emit(self.kind, self.key, *arguments)
        except RuntimeError:  # the application closed while the task ran
            pass


class TaskRunner(QObject):
    """Runs ``work(progress)`` off the UI thread.

    One task per kind runs at a time; submitting a new key of the same kind cancels the
    previous one through its progress callback. ``finished(kind, key, result, error)``
    reports every task; a cancelled task has neither result nor error.
    """

    finished = Signal(str, object, object, str)
    progress = Signal(str, object, float)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(3)
        self._signals = _Signals()
        self._signals.finished.connect(self._finished)
        self._signals.progress.connect(self.progress)
        self._running: dict[str, tuple[Any, threading.Event]] = {}

    def running(self, kind: str) -> Any:
        """The key of the task of this kind that is running, or None."""
        entry = self._running.get(kind)
        return entry[0] if entry else None

    def submit(self, kind: str, key: Any, work: Callable[[Callable[[float], bool]], Any]) -> None:
        if kind in self._running:
            if self._running[kind][0] == key:
                return
            self._running[kind][1].set()
        cancel = threading.Event()
        self._running[kind] = (key, cancel)
        self._pool.start(_Task(kind, key, work, self._signals, cancel))

    def _finished(self, kind: str, key: Any, result: Any, error: str) -> None:
        if self._running.get(kind, (None,))[0] == key:
            del self._running[kind]
        self.finished.emit(kind, key, result, error)

    def shutdown(self) -> None:
        for _key, cancel in self._running.values():
            cancel.set()
        self._pool.waitForDone(3000)
