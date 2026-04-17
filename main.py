import ctypes
import os
import sys
from pathlib import Path

import resources_rc
from dotenv import load_dotenv
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QApplication

from app.core.app import App
from app.ui.styles.fonts import load_fonts
from app.utils.crash_handler import install_crash_handlers, log_startup_diagnostics
from app.utils.cursor import create_custom_cursor
from app.utils.logger import get_logger, setup_logging
from app.utils.settings import get_language
from app.utils.window import window_resize
from translations.translation import init_translations


if getattr(sys, "frozen", False):
    load_dotenv(dotenv_path=Path(sys.executable).parent / ".env", override=False)
else:
    load_dotenv(override=False)

setup_logging()

_logger = get_logger(__name__)

def get_resource_path(relative: str) -> str:
    """Return absolute path to a resource."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(__file__), relative)


def _get_app_icon() -> QIcon:
    """Load and return the application icon."""
    ico_path = get_resource_path("resources/images/graphics/synapso.ico")
    return QIcon(ico_path)

def _force_taskbar_icon_for_frameless_window(window) -> None:
    """Ensure the window icon appears in the Windows taskbar when using a frameless window."""
    if sys.platform == "win32":
        hwnd = int(window.winId())
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE, (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
        )
        swp_nomove = 0x0002
        swp_nosize = 0x0001
        swp_nozorder = 0x0004
        swp_framechanged = 0x0020
        ctypes.windll.user32.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            swp_nomove | swp_nosize | swp_nozorder | swp_framechanged,
        )

def _acquire_single_instance_lock() -> object | None:
    """Create a Windows mutex to ensure only one application instance is running."""
    if sys.platform != "win32":
        return None
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\SynapsoApp")
    if ctypes.windll.kernel32.GetLastError() == 183:
        ctypes.windll.kernel32.CloseHandle(handle)
        return None
    return handle

def main():
    # Set a unique AppUserModelID on Windows for correct taskbar behavior
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Synapso.SynapsoApp.1"
        )

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Ínstall crash handlers after QApplication exists
    install_crash_handlers()
    log_startup_diagnostics()

    # Set window Icon
    app_icon = _get_app_icon()
    app.setWindowIcon(app_icon)

    # Initialize translations based on saved language preference or system language
    lang = get_language()
    init_translations(lang)

    # Get custom cursor for the entire application
    app.setOverrideCursor(create_custom_cursor())

    # Load custom fonts
    load_fonts()

    _logger.info("Creating main application window")
    window = App()
    window.setWindowIcon(app_icon)

    # Force taskbar icon
    _force_taskbar_icon_for_frameless_window(window=window)

    window.setMinimumSize(1600, 1000)
    window_resize(window=window, new_width=1600, new_height=1000)

    window.show()

    _logger.info("Entering Qt event loop")
    exit_code = app.exec()
    _logger.info("Application exited with code %d", exit_code)
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