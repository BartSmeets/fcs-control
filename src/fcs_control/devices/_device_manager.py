"""
Collect the devices
"""

from ._quantum import Quantum
from ._scope import Scope

DEVICE_CLS = {
            "Quantum": Quantum,
            "PrimaryScope": Scope,
            "SecondaryScope": Scope,
        }


class DeviceManager:
    def __init__(self):
        """
        Device Manager: sets attributes and tries to connect

        Attributes
        ----------
        Quantum: Quantum | None
            Quantum delay generator

        PrimaryScope: Scope |None
            Scope object

        SecondaryScope: Scope | None
            Scope object

        Methods
        -------
        connect_all: connects all devices

        disconnect_all: disconnects all devices

        """
        for key in DEVICE_CLS:
            setattr(self, key, None)

        self.connect_all()


    def connect_all(self):
        """
        Tries to connect all devices. 
        Assigns device object if available, None otherwise.
        """
        for key, cls in DEVICE_CLS.items():
            try:
                setattr(self, key, cls())
            except Exception:
                setattr(self, key, None)


    def disconnect_all(self):
        """
        Disconnect all devices.
        """
        for key, cls in self.__dict__.items():
            if cls:
                cls.disconnect()
                setattr(self, key, None)
