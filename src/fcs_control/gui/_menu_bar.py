"""
Build MenuBar

"""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar


class MenuBar(QMenuBar):
    """
    Builds MenuBar

    Contains: devices menu

    """
    def __init__(self, device_manager, parent=None):
        super().__init__(parent)

        self.device_manager = device_manager

        self.device_menu = self.addMenu("Devices")
        self.update_list()


    def update_list(self):
        """
        (Re)Builds devices list

        """
        self.device_menu.clear()

        # Active devices
        for key, info in self.device_manager.devices.items():
            if info["instance"] is not None:
                self.device_menu.addAction(key.capitalize())

        # Inactive devices
        self.inactive_device_sub = self.device_menu.addMenu("Inactive")
        for key, info in self.device_manager.devices.items():
            if info["instance"] is None:
                self.inactive_device_sub.addAction(key.capitalize())

        # Reconnect Button
        self.device_menu.addSeparator()
        reconnect_action = QAction("Reconnect", self)
        reconnect_action.triggered.connect(self.reconnect)
        self.device_menu.addAction(reconnect_action)

    def reconnect(self):
        """
        Reconnect all devices, and update list.
        
        """
        self.device_manager.connect_all()
        self.update_list()