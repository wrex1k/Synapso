import sys
from PySide6.QtWidgets import QApplication
from app.db import schema, seed
from app.mainWindow import MainWindow

def main():
    schema.create_tables()
    seed.seed_initial_data()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
