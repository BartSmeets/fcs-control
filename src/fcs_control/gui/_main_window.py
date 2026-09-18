"""
Builds the Main Window

"""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from ..devices import get_device_manager
from ._delay_panel import DelayPanel
from ._experiment_panel import ExperimentPanel
from ._log_panel import LogPanel
from ._menu_bar import MenuBar
from ._voltage_panel import VoltagePanel


class MainWindow(QMainWindow):
    """
    Builds the main window.

    Combines `LogPanel`, `VoltagePanel`, `MaterialPanel`, and `DelayPanel`.

    """
    def __init__(self):
        super().__init__()

        # Page Settings
        self.setWindowTitle("FCS: Free Cluster Setup")
        layout = QHBoxLayout()

        # Panels
        layout.addWidget(LogPanel(self))
        self.device_manager = get_device_manager()  # Load device manager after logpanel to add to log already

        self.voltage_panel = VoltagePanel(self)
        self.delay_panel = DelayPanel(self)
        self.experiment_panel = ExperimentPanel(self)

        layout.addWidget(self.voltage_panel)
        layout.addWidget(self.delay_panel)
        layout.addWidget(self.experiment_panel)

        # Cobined Panels as Widget
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Menu Bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

    def get_all_settings(self):
        return {
            "voltages": self.voltage_panel.get_settings(),
            "delays": self.delay_panel.get_settings(),
            "experiment": self.experiment_panel.get_settings(),
        }
