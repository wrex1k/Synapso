import logging
import os
import platform
import sys
import threading
import traceback
from datetime import datetime

from app.utils.logger import get_log_dir, get_user_context
from app.utils.breadcrumbs import add_breadcrumb, format_breadcrumbs

logger = logging.getLogger("synapso.crash")

_active_view: str = "unknown"


def set_active_view(view_name: str) -> None:
    global _active_view
    _active_view = view_name


def get_active_view() -> str:
    return _active_view


_last_backend_op: str = "none"


def set_last_backend_op(op: str) -> None:
    global _last_backend_op
    _last_backend_op = op


def get_last_backend_op() -> str:
    return _last_backend_op


def write_crash_dump(exc_type, exc_value, exc_tb, thread_name: str = "MainThread") -> str | None:
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
            "── Recent events before crash ──",
            format_breadcrumbs(),
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
        "── Recent events before crash ──\n"
        f"{format_breadcrumbs()}\n"
    )
    logger.critical(summary)

    dump_path = write_crash_dump(exc_type, exc_value, exc_tb, thread_name)
    if dump_path:
        logger.critical("Crash dump written to: %s", dump_path)


_original_excepthook = sys.excepthook


def _main_thread_excepthook(exc_type, exc_value, exc_tb):
    add_breadcrumb("crash", f"Unhandled exception: {exc_type.__name__}: {exc_value}")
    _log_crash_summary(exc_type, exc_value, exc_tb, thread_name="MainThread")
    _original_excepthook(exc_type, exc_value, exc_tb)


def _threading_excepthook(args):
    exc_type = args.exc_type
    exc_value = args.exc_value
    exc_tb = args.exc_traceback
    thread = args.thread
    thread_name = thread.name if thread else "UnknownThread"

    if exc_type is SystemExit:
        return

    add_breadcrumb("crash", f"Unhandled exception in thread {thread_name}: {exc_type.__name__}: {exc_value}")
    _log_crash_summary(exc_type, exc_value, exc_tb, thread_name=thread_name)


def install_crash_handlers() -> None:
    sys.excepthook = _main_thread_excepthook
    threading.excepthook = _threading_excepthook
    logger.debug("Crash handlers installed (sys.excepthook + threading.excepthook)")


def log_startup_diagnostics() -> None:
    frozen = getattr(sys, "frozen", False)
    exe_path = sys.executable if frozen else sys.argv[0] if sys.argv else __file__

    is_dev = not frozen
    build_type = "development (script)" if is_dev else "production (frozen)"

    screen_info = "unknown"
    try:
        from PySide6.QtWidgets import QApplication
        app_instance = QApplication.instance()
        if app_instance:
            screen = app_instance.primaryScreen()
            if screen:
                geom = screen.geometry()
                screen_info = f"{geom.width()}x{geom.height()}"
    except Exception:
        pass

    language = "unknown"
    try:
        from app.utils.settings import get_language
        language = get_language()
    except Exception:
        pass

    version = "unknown"
    try:
        from app import __version__
        version = __version__
    except Exception:
        version = "dev"

    diag = (
        "\n"
        "┌──────────────────────────────────────────────────────────────┐\n"
        "│                   SYNAPSO STARTUP                           │\n"
        "└──────────────────────────────────────────────────────────────┘\n"
        f"  Version:      {version}\n"
        f"  Build:        {build_type}\n"
        f"  Python:       {platform.python_version()}\n"
        f"  OS:           {platform.platform()}\n"
        f"  Architecture: {platform.machine()}\n"
        f"  CWD:          {os.getcwd()}\n"
        f"  Executable:   {exe_path}\n"
        f"  Screen:       {screen_info}\n"
        f"  Language:     {language}\n"
        f"  Log dir:      {get_log_dir()}\n"
    )
    logger.info(diag)
    add_breadcrumb("app", "Application started")