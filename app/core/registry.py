from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from app.utils.logger import get_logger

logger = get_logger(__name__)



class _Runner(QObject):
    """Worker object that executes a function in a separate thread."""
    finished = Signal(object)

    def __init__(self, fn: Callable[[], object]):
        super().__init__()
        self._fn = fn

    @Slot()
    def run(self):
        try:
            result = self._fn()

        except Exception:
            logger.exception("Unhandled exception in thread task")
            result = None
        self.finished.emit(result)


class _CallbackProxy(QObject):
    """Proxy object for safely dispatching callbacks from thread results."""
    def __init__(self, callback: Callable[[object], None]):
        super().__init__()
        self._callback = callback

    @Slot(object)
    def dispatch(self, result: object) -> None:
        self._callback(result)

class Operation:
    """Manages a single background operation with thread lifecycle control."""
    def __init__(self, key: str | None = None):
        self._key = key
        self._thread: Optional[QThread] = None

    def is_running(self) -> bool:
        """Check if the operation's thread is currently running."""
        if self._thread is None:
            return False
        try:
            return self._thread.isRunning()
        except RuntimeError:
            self._thread = None
            return False

    def start(
        self,
        run_thread_fn: Callable[..., QThread],
        fn: Callable[[], object],
        on_finished: Callable[[object], None] | None = None,
        *,
        name: str | None = None,
    ) -> bool:
        """Start the operation if not already running, returning True if started."""
        if self.is_running():
            return False
        
        logger.debug("Starting operation %s with %s", self._key, name)

        thread = run_thread_fn(fn, on_finished, name=name)
        self._thread = thread

        def _clear():
            if self._thread is thread:
                self._thread = None

        thread.finished.connect(_clear)
        return True

    def cancel(self, wait_ms: int = 2000) -> None:
        """Cancel the running operation and wait for the thread to finish."""
        t = self._thread
        if not t:
            return

        if t.isRunning():
            logger.debug("Stopping thread: %s", t.objectName() or repr(t))
            t.quit()

            if not t.wait(wait_ms):
                logger.warning("Thread did not stop within %d ms: %s", wait_ms, t.objectName() or repr(t))

        self._thread = None


class Registry:
    """Central registry for managing background operations and cleanup handlers."""
    def __init__(self):
        self._handlers: list[Callable[[], None]] = []
        self._ops: dict[str, Operation] = {}

    def register(self, fn: Callable[[], None]) -> None:
        """Register a cleanup handler to be called during shutdown."""
        if callable(fn):
            self._handlers.append(fn)

    def cleanup(self) -> None:
        """Execute all registered cleanup handlers."""
        for fn in list(self._handlers):
            try:
                fn()
            except Exception:
                logger.exception("Error during cleanup handler: %r", fn)

    def operation(self, key: str) -> Operation:
        """Get or create an operation identified by the given key."""
        op = self._ops.get(key)
        if op is None:
            op = Operation(key=key)
            self._ops[key] = op
            self.register(op.cancel)
        return op

    def run_thread(self, fn: Callable[[], object], on_finished: Callable[[object], None] | None = None, *, name: str | None = None) -> QThread:
        """Create and start a new thread that executes the given function."""
        thread = QThread()
        if name:
            thread.setObjectName(name)

        worker = _Runner(fn)
        worker.moveToThread(thread)

        thread._worker = worker

        thread.started.connect(worker.run)

        if callable(on_finished):
            callback_proxy = _CallbackProxy(on_finished)
            thread._callback_proxy = callback_proxy
            worker.finished.connect(callback_proxy.dispatch, Qt.QueuedConnection)
            if name:
                callback_proxy.destroyed.connect(lambda *_: logger.debug("%s finished", name.capitalize()))

        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.start()
        return thread


registry = Registry()