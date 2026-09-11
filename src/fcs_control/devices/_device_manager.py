"""
Collect the devices
"""

__all__ = ["get_device_manager"]

import logging
import threading
from contextlib import contextmanager

from ._quantum import Quantum
from ._scope import Scope

DEVICE_CLS = {
            "quantum": {
                "class": Quantum,
                "kwargs": {},
                "description": "Quantum 9520 Delay Generator",
                "occupied": False,
            },
            "primaryscope": {
                "class": Scope,
                "kwargs": {"prisec": "primary"},
                "description": "Primary MDO34 Scope",
                "occupied": False,
            },
            "secondaryscope": {
                "class": Scope,
                "kwargs": {"prisec": "secondary"},
                "description": "Secondary MDO34 Scope",
                "occupied": False,
            },
        }

_logger = logging.getLogger(__name__)

class DeviceManager:
    quantum: Quantum | None
    primaryscope: Scope | None
    secondaryscope: Scope | None

    def __init__(self):
        """
        Device Manager: sets attributes and tries to connect

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
        self._lock = threading.Lock()
        self.connect_all()

    def get_device(self, key):
        try:
            info = self.devices[key]
        except KeyError:
            raise AttributeError(
                f"{type(self).__name__!r} has no attribute {key!r}"
                )

        if info["occupied"]:
            raise RuntimeError(
                f"{key} is being used in a running experiment"
                )

        return info["instance"]

    @property
    def online(self):
        """
        Dict of currently connected devices: {key: instance}

        """
        return {
            key: info["instance"]
            for key, info in self.devices.items()
            if info["instance"] is not None
        }

    @property
    def offline(self):
        """
        List of keys for devices that are not currently connected.

        """
        return [
            key for key, info in self.devices.items()
            if info["instance"] is None
        ]

    @contextmanager
    def reserve(self, key: str):
        info = self.devices[key]

        with self._lock:
            if info["occupied"]:
                raise RuntimeError(f"{key} is already occupied")
            info["occupied"] = True

        try:
            yield info["instance"]
        finally:
            info["occupied"] = False

    def is_connected(self, key):
        """
        Whether a specific device (by key) is currently connected.

        """
        return self.devices[key]["instance"] is not None
    
    def connect_all(self):
        """
        Tries to connect all devices. 
        Assigns device object if available, None otherwise.
        
        """
        for key, info in self.devices.items():
            try:
                cls = info["class"]
                kwargs = info["kwargs"]

                if info["occupied"]:
                    continue
                info["instance"] = cls(**kwargs)

                _logger.info(f"{key} successfully connected")

            except Exception as e: # noqa: BLE001
                info["instance"] = None
                _logger.warning(f"{key} not connected: {e}")

    def disconnect_all(self):
        """
        Disconnect all devices.

        """
        for key, info in self.devices.items():
            instance = info["instance"]
            if instance and not info["occupied"]:
                instance.disconnect()
                info["instance"] = None
                _logger.info(f"{key} disconnected")

    def check_connection(self, key):
        """
        Verify whether a device is still responsive.
        Updates the registry (marks as disconnected) if it is not.

        Returns
        -------
        bool
            True if the device is connected and responsive.

        """
        info = self.devices[key]
        if info["occupied"]:
            raise RuntimeError(f"{key} is already occupied")

        instance = info["instance"]
        if instance is None:
            return False
        if not instance.is_alive():
            self.devices[key]["instance"] = None
            _logger.warning(f"{key} has lost connection at some point.")
            return False
        return True

    def refresh_status(self):
        """
        Actively re-check every device's connection status.

        """
        for key in self.devices:
            self.check_connection(key)

_device_manager = None

def get_device_manager() -> DeviceManager:
    """
    Use this to get the global device manager.
    
    """
    global _device_manager

    if _device_manager is None:
        _device_manager = DeviceManager()

    return _device_manager
