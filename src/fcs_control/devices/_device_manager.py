"""
Collect the devices
"""

__all__ = ["get_device_manager"]

import logging

from ._quantum import Quantum
from ._scope import Scope

DEVICE_CLS = {
            "quantum": {
                "class": Quantum,
                "kwargs": {},
                "description": "Quantum 9520 Delay Generator"
            },
            "primaryscope": {
                "class": Scope,
                "kwargs": {"prisec": "primary"},
                "description": "Primary MDO34 Scope"
            },
            "secondaryscope": {
                "class": Scope,
                "kwargs": {"prisec": "secondary"},
                "description": "Secondary MDO34 Scope"
            },
        }

_logger = logging.getLogger(__name__)

class _DeviceManager:
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

        get_devices: dictionary of devices

        """
        self.devices = {
            key: {**info, "instance": None}
            for key, info in DEVICE_CLS.items()
        }

        self.connect_all()

    def __getattr__(self, name):
        try:
            return self.devices[name]["instance"]
        except KeyError:
            raise AttributeError(
                f"{type(self).__name__!r} has no attribute {name!r}"
            )
        
    def connect_all(self):
        """
        Tries to connect all devices. 
        Assigns device object if available, None otherwise.
        
        """
        for key, info in self.devices.items():
            try:
                cls = info["class"]
                kwargs = info["kwargs"]

                info["instance"] = cls(**kwargs)

                _logger.info(f"{key} successfully connected")

            except Exception as e:
                info["instance"] = None
                _logger.warning(f"{key} not connected: {e}")

    def disconnect_all(self):
        """
        Disconnect all devices.
        """
        for key, cls in self.__dict__.items():
            if cls:
                cls.disconnect()
                setattr(self, key, None)


_device_manager = None

def get_device_manager():
    global _device_manager

    if _device_manager is None:
        _device_manager = _DeviceManager()

    return _device_manager
