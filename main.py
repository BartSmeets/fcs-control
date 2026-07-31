"""
Main app

"""

import sys

from PySide6.QtWidgets import (
    QApplication,
)

from fcs_control.gui import MainWindow


# Run Application
def main():
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()