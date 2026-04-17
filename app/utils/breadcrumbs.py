"""
Ring buffer posledných udalostí pred crashom.

Thread-safe deque zachytáva posledných N významných eventov.
Pri páde sa dumpia do logu pod sekciu "Recent events before crash".
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field


_MAX_BREADCRUMBS = 150

@dataclass(slots=True)
class Breadcrumb:
    timestamp: float
    category: str
    message: str
    data: dict = field(default_factory=dict)

    def format(self) -> str:
        ts = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        ms = int((self.timestamp % 1) * 1000)
        base = f"[{ts}.{ms:03d}] [{self.category}] {self.message}"
        if self.data:
            extras = ", ".join(f"{k}={v}" for k, v in self.data.items())
            base += f" ({extras})"
        return base


_lock = threading.Lock()
_buffer: deque[Breadcrumb] = deque(maxlen=_MAX_BREADCRUMBS)


def add_breadcrumb(category: str, message: str, **data) -> None:
    crumb = Breadcrumb(
        timestamp=time.time(),
        category=category,
        message=message,
        data=data,
    )
    with _lock:
        _buffer.append(crumb)


def get_breadcrumbs() -> list[Breadcrumb]:
    with _lock:
        return list(_buffer)


def format_breadcrumbs() -> str:
    crumbs = get_breadcrumbs()
    if not crumbs:
        return "  (no breadcrumbs recorded)"
    lines = [f"  {c.format()}" for c in crumbs]
    return "\n".join(lines)


def clear() -> None:
    with _lock:
        _buffer.clear()
