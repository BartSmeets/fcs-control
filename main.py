"""
Main app

"""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from fcs_control.devices import get_device_manager
from fcs_control.gui import MenuBar, logPanel, voltagePanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FCS: Free Cluster Setup")

        layout = QHBoxLayout()
        layout.addWidget(logPanel(self))
        layout.addWidget(voltagePanel())
        
        self.device_manager = get_device_manager()
        
        self.menu_bar = MenuBar(self.device_manager, self)
        self.setMenuBar(self.menu_bar)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

app = QApplication([])

window = MainWindow()
window.showMaximized()

sys.exit(app.exec())