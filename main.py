import sys
from PySide6.QtWidgets import QApplication
# from app.db.schema import initialize_database
from app.core.app import App
from app.utils import load_fonts, get_clash_grotesk 

def main():
    # initialize_database()

    app = QApplication(sys.argv)
    
    # Load custom fonts
    load_fonts()
    
    # Set default font for the entire application
    default_font = get_clash_grotesk()
    app.setFont(default_font)
    
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()