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
from fcs_control.gui import DelayPanel, LogPanel, MaterialPanel, MenuBar, VoltagePanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Page Settings
        self.setWindowTitle("FCS: Free Cluster Setup")
        layout = QHBoxLayout()

        # Panels
        ## Log Panel
        layout.addWidget(LogPanel(self))
        self.device_manager = get_device_manager()  # Load device manager after logpanel to add to log

        layout.addWidget(VoltagePanel(self))
        layout.addWidget(MaterialPanel(self))
        layout.addWidget(DelayPanel(self))

        # Cobined Panels as Widget
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Menu Bar
        self.menu_bar = MenuBar(self.device_manager, self)
        self.setMenuBar(self.menu_bar)


# Run Application
def main():
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()