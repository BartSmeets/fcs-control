import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QMessageBox

from ..config import NETWORK
from ..devices._device_manager import get_device_manager

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
    name: str = "My name is Jeff"
    description: str = ""

    required_devices: tuple = ()
    parameters: tuple[type[Parameter]] = ()

    data_folder: str | None = None

    # Every experiment must have a title and comment
    _base_parameters = (
        Parameter('title',
                  'File Name',
                  'short_text',
                  ''),
        Parameter('comment',
                  'Babbelbox',
                  'long_text',
                  ''),
    )

    def __init__(self, main_window=None):
        self.parent_window = main_window

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

    def prep_folder(self):
        """
        Set the folder to store the data and logs.

        """
        # What's the date please?
        today = date.today()  # noqa: DTZ011

        # Retrieve data location
        base = Path(NETWORK.data_folder)
        while not os.path.exists(base):
            _logger.warning(f"Cannot connect to {base}. Is the PC offline by any chance?")

            answer = QMessageBox.question(self.parent_window, 
                                          'Network Folder Not Found',
                                          f"Cannot connect to: {base}\n\n"
                                          f"Do you want to try again?\n"
                                          f"Yes = Retry network folder\n"
                                          f"No = Use local folder",
                                          QMessageBox.Yes | QMessageBox.No)

            if answer == QMessageBox.No and base != Path(NETWORK.no_network_folder):
                base = Path(NETWORK.no_network_folder)
            else:
                raise OSError("Neither the only nor offline folder can be reached...")

        # Create subfolders
        year_folder = base / str(today.year)
        month_folder = year_folder / today.strftime("%b")
        day_folder = month_folder / today.strftime("%d%m")

        day_folder.mkdir(parents = True, exist_ok = True)
        self.data_folder = day_folder

        _logger.info(f"Using experiment folder: {day_folder}")


    @abstractmethod
    def scan(self,
            parameters: dict[str, Any],
            ):
        raise NotImplementedError

    def execute(self, parameters):
        """
        The code that runs when an experiment is initiated from the UI.
        
        """
        # Prepare data folder
        try:
            self.prep_folder()
        except OSError as e:
            self.exp_logger.exception("OS Error")
            QMessageBox.warning(self.parent, "OS Error", str(e))
            return


        filename = ''   # TODO: Read filename from input

        # Intiate logger
        self.exp_logger = logging.getLogger(f"experiment.{filename}")
        self.exp_logger.setLevel(logging.INFO)
        self.exp_logger.propagate = True

        handler = logging.FileHandler(self.data_folder / f"{filename}_log.txt", encoding="utf-8")
        self.exp_logger.addHandler(handler)

        # Prep devices and 
        
        try:
            self.validate_devices()
        except OSError as e:
            self.exp_logger.exception("Device Error")
            QMessageBox.warning(self.parent, "Device Error", str(e))
            return

        # Run Scan
        self.scan(parameters)




# ===================
# Registry
# ===================
EXPERIMENT_REGISTRY: dict[str, type[Experiment]] = {}


def register_experiment(experiment: type[Experiment]) -> type[Experiment]:
    if experiment.name in EXPERIMENT_REGISTRY:
        raise ValueError(f"Duplicate experiment name: {experiment.name}")
    EXPERIMENT_REGISTRY[experiment.name] = experiment
    return experiment