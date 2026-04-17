import ctypes
import os
import sys

from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QApplication

import resources_rc

from app.core.app import App
from app.utils.cursor import create_custom_cursor
from app.ui.styles.fonts import load_fonts

from app.utils.settings import get_language
from translations.translation import init_translations

from app.utils.dev import simulate_resolution

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # initialize translations based on saved language preference or system language
    init_translations(get_language())
    
    # set application ID for Windows taskbar grouping
    if sys.platform == "win32":
        app_id = "Synapso.app"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
    # get custom cursor for the entire application
    app.setOverrideCursor(create_custom_cursor())
    
    # load custom fonts
    load_fonts()

    window = App()
    window.show()
    
    simulate_resolution(window, "1600x1000")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()