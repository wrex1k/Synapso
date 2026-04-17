import ctypes
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from app.utils.logging_config import setup_logging, get_logger

if getattr(sys, "frozen", False):
    load_dotenv(dotenv_path=Path(sys.executable).parent / ".env", override=False)
else:
    load_dotenv(override=False)

setup_logging()

_logger = get_logger("synapso.main")

from app.utils.crash_handler import install_crash_handlers, log_startup_diagnostics
from app.utils.breadcrumbs import add_breadcrumb

from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QApplication

import resources_rc

from app.core.app import App
from app.ui.styles.fonts import load_fonts

from app.utils.settings import get_language
from app.utils.window import window_resize
from app.utils.cursor import create_custom_cursor

from translations.translation import init_translations

def get_resource_path(relative: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(__file__), relative)


def _get_app_icon() -> QIcon:
    ico_path = get_resource_path("resources/images/graphics/logo.ico")

    if os.path.isfile(ico_path):
        return QIcon(ico_path)

    return QIcon(":/images/graphics/logo.png")


def _acquire_single_instance_lock() -> object | None:
    if sys.platform != "win32":
        return None
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\SynapsoApp")
    if ctypes.windll.kernel32.GetLastError() == 183:
        ctypes.windll.kernel32.CloseHandle(handle)
        return None
    return handle


def main():
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Synapso.SynapsoApp.1"
        )

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Install crash handlers after QApplication exists
    install_crash_handlers()
    log_startup_diagnostics()

    # set window Icon
    app.setWindowIcon(_get_app_icon())

    # initialize translations based on saved language preference or system language
    init_translations(get_language())
    add_breadcrumb("app", "Translations initialized", language=get_language())

    # get custom cursor for the entire application
    app.setOverrideCursor(create_custom_cursor())

    # load custom fonts
    load_fonts()
    add_breadcrumb("app", "Fonts loaded")

    _logger.info("Creating main application window")
    window = App()

    window.setMinimumSize(1600, 1000)
    window_resize(window, 1600, 1000)

    window.show()

    _logger.info("Entering Qt event loop")
    add_breadcrumb("app", "Qt event loop started")
    exit_code = app.exec()
    _logger.info("Application exited with code %d", exit_code)
    add_breadcrumb("app", "Application exited", exit_code=exit_code)
    sys.exit(exit_code)

if __name__ == "__main__":
    _lock = _acquire_single_instance_lock()
    if _lock is None:
        sys.exit(0)
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        _logger.critical("Fatal error during application startup", exc_info=True)
        from app.utils.crash_handler import write_crash_dump
        write_crash_dump(*sys.exc_info(), thread_name="MainThread")
        sys.exit(1)