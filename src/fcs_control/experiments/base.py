from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QMessageBox

from ..devices._device_manager import get_device_manager
from ..utils.data_management import data_folder, file_name, save_production_settings

if TYPE_CHECKING:
    from ..gui import MainWindow  # adjust relative path

_logger = logging.getLogger(__name__)

@dataclass
class Parameter:
    name: str
    label: str
    type: str
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str = ""
    options: list | None = None


class Experiment(ABC):
    # Has to be defined manually
    name: str = "My name is Jeff"
    description: str = ""
    required_devices: tuple = ()
    parameters: tuple[type[Parameter]] = ()

    # Every experiment must have a title and comment
    _base_parameters: tuple[type[Parameter]] = (    
        Parameter('title',
                  'File Name',
                  'short_text',
                  ''),
        Parameter('comment',
                  'Babbelbox',
                  'long_text',
                  ''),
        )

    # Will be generated during run
    data_folder: str | None = None


    def __init__(self, main_window: MainWindow | None = None):
        self.main_window = main_window
        try:
            self.settings = main_window.get_all_settings()
        except AttributeError:
            self.settings = {}

    @property
    def all_parameters(self) -> tuple[type[Parameter], ...]:
        """
        Every parameter this experiment needs: the always-required
        base parameters (file name, comment) plus whatever the
        subclass declared in `parameters`.

        """
        extra = tuple(p for p in self.parameters if p not in self._base_parameters)
        return self._base_parameters + extra
    
    def validate_devices(self):
        """
        Check if all required devices are connected

        """
        device_manager = get_device_manager()
        disconnected = [
            device_name for device_name in self.required_devices
            if not device_manager.check_connection(device_name)
            ]
        if disconnected:
            raise OSError(f"At least one required device is not connected: {disconnected}")


    @abstractmethod
    def scan(self):
        raise NotImplementedError

    # Set up Logbook
    @contextmanager
    def _file_logging(self, log_path):
        # Write settings from the GUI as a plain header
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Settings ===\n")
            f.write(json.dumps(self.settings, indent=2, default=str))
            f.write("\n=== Log ===\n")

        handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        handler.setFormatter(...)
        _logger.addHandler(handler)
        try:
            yield                          
        finally:
            _logger.removeHandler(handler)
            handler.close()

    def execute(self):
        """
        The code that runs when an experiment is initiated from the UI.
        
        """
        # Prepare data folder
        try:
            self.data_folder = data_folder(self.main_window)
        except OSError as e:
            _logger.exception("OS Error")
            QMessageBox.warning(self.main_window, "OS Error", str(e))
            return
        self.filename = file_name(self.data_folder, self.settings["experiment"]["title"])

        # Intiate logger
        save_production_settings(self.data_folder, self.filename, self.settings)
        with self._file_logging(self.data_folder / f"{self.filename}_log.txt"):

            # Validate devices
            try:
                self.validate_devices()
            except OSError as e:
                _logger.exception("Device Error")
                QMessageBox.warning(self.main_window, "Device Error", str(e))
                return

            # Run Scan
            self.scan()
            _logger.info("Scan finished succesfully. HOORAY!")

            # Final comment




# ===================
# Registry
# ===================
EXPERIMENT_REGISTRY: dict[str, type[Experiment]] = {}


def register_experiment(experiment: type[Experiment]) -> type[Experiment]:
    if experiment.name in EXPERIMENT_REGISTRY:
        raise ValueError(f"Duplicate experiment name: {experiment.name}")
    EXPERIMENT_REGISTRY[experiment.name] = experiment
    return experiment