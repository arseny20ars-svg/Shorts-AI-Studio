import sys
from PySide6.QtWidgets import QApplication
from shorts_ai.ui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Shorts AI Studio")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
