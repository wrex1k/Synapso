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

    #Standard displays:
    #simulate_resolution(window, "hd")        # 1366x768 (most common laptop)
    #simulate_resolution(window, "fhd")       # 1920x1080 (Full HD)
    #simulate_resolution(window, "small")     # 1280x720 (smaller displays)
    #simulate_resolution(window, "qhd")       # 2560x1440 (2K)
    #simulate_resolution(window, "4k")        # 3840x2160 (4K UHD)
    
    # Ultra Wide displays:
    #simulate_resolution(window, "uwfhd")     # 2560x1080 (21:9 UltraWide FHD)
    #simulate_resolution(window, "uwqhd")     # 3440x1440 (21:9 UltraWide QHD)
    #simulate_resolution(window, "superuw")   # 5120x2160 (32:9 Super UltraWide)
    
    # Custom resolution:
    #simulate_resolution(window, "1440x900")  # Custom WIDTHxHEIGHT

    sys.exit(app.exec())

if __name__ == "__main__":
    main()