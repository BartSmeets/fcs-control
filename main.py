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
from fcs_control.gui import LogPanel, MaterialPanel, MenuBar, VoltagePanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FCS: Free Cluster Setup")

        layout = QHBoxLayout()
        layout.addWidget(LogPanel(self))
        layout.addWidget(VoltagePanel(self))
        layout.addWidget(MaterialPanel(self))

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        self.device_manager = get_device_manager()
        
        self.menu_bar = MenuBar(self.device_manager, self)
        self.setMenuBar(self.menu_bar)


app = QApplication([])

window = MainWindow()
window.showMaximized()

sys.exit(app.exec())