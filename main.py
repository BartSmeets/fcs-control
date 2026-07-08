"""
Main app

"""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from fcs_control.devices import get_device_manager
from fcs_control.gui import MenuBar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FCS: Free Cluster Setup")
        self.device_manager = get_device_manager()
        
        self.menu_bar = MenuBar(self.device_manager, self)
        self.setMenuBar(self.menu_bar)


app = QApplication([])

window = MainWindow()
window.showMaximized()

print("start mainloop")
sys.exit(app.exec())