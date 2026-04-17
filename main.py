import ctypes
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from app.utils.logger import setup_logging, get_logger

if getattr(sys, "frozen", False):
    load_dotenv(dotenv_path=Path(sys.executable).parent / ".env", override=False)
else:
    load_dotenv(override=False)

setup_logging()

_logger = get_logger(__name__)

from app.utils.crash_handler import install_crash_handlers, log_startup_diagnostics
from app.utils.breadcrumbs import add_breadcrumb

from PySide6.QtGui import Qt, QIcon, QPalette, QColor
from PySide6.QtWidgets import QApplication, QStyleFactory

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
    for name in ("synapso.ico", "logo.ico"):
        ico_path = get_resource_path(f"resources/images/graphics/{name}")
        if os.path.isfile(ico_path):
            return QIcon(ico_path)

    icon = QIcon(":/images/graphics/logo.png")
    if not icon.isNull():
        return icon

    return QIcon()


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

    # override system-dependent widget colors with Fusion style and a custom dark palette
    app.setStyle(QStyleFactory.create("Fusion"))

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window,          QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.WindowText,      QColor(250, 250, 250))
    dark_palette.setColor(QPalette.ColorRole.Base,            QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(40, 40, 40))
    dark_palette.setColor(QPalette.ColorRole.Text,            QColor(250, 250, 250))
    dark_palette.setColor(QPalette.ColorRole.Button,          QColor(50, 50, 50))
    dark_palette.setColor(QPalette.ColorRole.ButtonText,      QColor(250, 250, 250))
    dark_palette.setColor(QPalette.ColorRole.BrightText,      QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Highlight,       QColor(34, 117, 111))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(250, 250, 250))
    app.setPalette(dark_palette)

    # install crash handlers after QApplication exists
    install_crash_handlers()
    log_startup_diagnostics()

    # set window Icon
    app.setWindowIcon(_get_app_icon())

    # initialize translations based on saved language preference or system language
    lang = get_language()
    init_translations(lang)
    add_breadcrumb("app", "Translations initialized", language=lang)

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