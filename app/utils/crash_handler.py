import logging
import os
import platform
import sys
import threading
import traceback
from datetime import datetime

from app.utils.logger import get_log_dir, get_user_context

logger = logging.getLogger("synapso.crash")

_active_view: str = "unknown"


def set_active_view(view_name: str) -> None:
    """Set the currently active UI view name for crash context."""
    global _active_view
    _active_view = view_name


_last_backend_op: str = "none"


def set_last_backend_op(op: str) -> None:
    """Set the last backend operation name for crash context."""
    global _last_backend_op
    _last_backend_op = op


def write_crash_dump(exc_type, exc_value, exc_tb, thread_name: str = "MainThread") -> str | None:
    """Write a crash dump file with exception details and return the file path."""
    try:
        log_dir = get_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dump_path = os.path.join(log_dir, f"crash_{ts}.log")

        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        user_id = get_user_context() or "not-logged-in"

        lines = [
            "=" * 80,
            "SYNAPSO CRASH REPORT",
            "=" * 80,
            f"Timestamp:       {datetime.now().isoformat()}",
            f"Thread:          {thread_name}",
            f"User ID:         {user_id}",
            f"Active view:     {_active_view}",
            f"Last backend op: {_last_backend_op}",
            "",
            "── Exception ──",
            f"Type:    {exc_type.__name__ if exc_type else 'Unknown'}",
            f"Message: {exc_value}",
            "",
            "── Traceback ──",
            tb_text,
            "",
            "── Environment ──",
            f"Python:   {sys.version}",
            f"Platform: {platform.platform()}",
            f"Frozen:   {getattr(sys, 'frozen', False)}",
            f"CWD:      {os.getcwd()}",
            "=" * 80,
        ]

        with open(dump_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return dump_path

    except Exception:
        return None


def _log_crash_summary(exc_type, exc_value, exc_tb, thread_name: str = "MainThread"):
    """Log a formatted crash summary and write a crash dump file."""
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    user_id = get_user_context() or "not-logged-in"

    summary = (
        "\n"
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║                    UNHANDLED EXCEPTION                      ║\n"
        "╚══════════════════════════════════════════════════════════════╝\n"
        f"  Thread:       {thread_name}\n"
        f"  User:         {user_id}\n"
        f"  Active view:  {_active_view}\n"
        f"  Last op:      {_last_backend_op}\n"
        f"  Exception:    {exc_type.__name__ if exc_type else 'Unknown'}: {exc_value}\n"
        "\n"
        "── Traceback ──\n"
        f"{tb_text}\n"
    )
    logger.critical(summary)

    dump_path = write_crash_dump(exc_type, exc_value, exc_tb, thread_name)
    if dump_path:
        logger.critical("Crash dump written to: %s", dump_path)


_original_excepthook = sys.excepthook


def _main_thread_excepthook(exc_type, exc_value, exc_tb):
    """Custom sys.excepthook that logs crash summary before calling the original hook."""
    _log_crash_summary(exc_type, exc_value, exc_tb, thread_name="MainThread")
    _original_excepthook(exc_type, exc_value, exc_tb)


def _threading_excepthook(args):
    """Custom threading.excepthook that logs crash summary for worker threads."""
    exc_type = args.exc_type
    exc_value = args.exc_value
    exc_tb = args.exc_traceback
    thread = args.thread
    thread_name = thread.name if thread else "UnknownThread"

    if exc_type is SystemExit:
        return

    _log_crash_summary(exc_type, exc_value, exc_tb, thread_name=thread_name)


def install_crash_handlers() -> None:
    """Install global exception handlers for the main thread and worker threads."""
    sys.excepthook = _main_thread_excepthook
    threading.excepthook = _threading_excepthook
    logger.debug("Crash handlers installed (sys.excepthook + threading.excepthook)")


def log_startup_diagnostics() -> None:
    """Log system environment info at application startup."""
    frozen = getattr(sys, "frozen", False)

    diag = (
        "\n"
        "┌──────────────────────────────────────────────────────────────┐\n"
        "│                   SYNAPSO STARTUP                           │\n"
        "└──────────────────────────────────────────────────────────────┘\n"
        f"  Python:   {platform.python_version()}\n"
        f"  OS:       {platform.platform()}\n"
        f"  Frozen:   {frozen}\n"
        f"  CWD:      {os.getcwd()}\n"
        f"  Log dir:  {get_log_dir()}\n"
    )
    logger.info(diag)