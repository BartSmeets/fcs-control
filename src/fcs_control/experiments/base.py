"""
Defines the "rules" for defining experiments.

Contains
--------
Parameter: Class
    Class for communicating required parameters to the GUI
Experiment: Class
    Class for defining the Experiment

To define an experiment:
Add an experiment file `<experiment>.py`, containing an `Experiment` class definition

"""
from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QEventLoop, QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QDialog, QMessageBox, QProgressDialog

from ..devices._device_manager import get_device_manager
from ..gui.popup import CommentBox
from ..utils.data_management import data_folder, file_name, save_production_settings

if TYPE_CHECKING:
    from ..gui import MainWindow  # adjust relative path

_logger = logging.getLogger(__name__)


@dataclass
class Parameter:
    """
    Parameter data class

    This class is used to communicate required parameters for an experiment to the GUI
    
    """
    name: str
    label: str
    type: str
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str = ""
    options: list | None = None


class _ScanWorker(QObject):
    """
    Runs `Experiment.scan()` on a background thread.

    Lives on a `QThread` (via `moveToThread`), so everything happening inside
    `run()` - including the experiment's `scan()` - executes off the GUI
    thread. Communicates back to the GUI thread exclusively via signals.

    """
    progress = Signal(int, int, str)   # current, total, label text
    finished = Signal(object)          # scan() return value
    failed = Signal(str)               # str(exception)

    def __init__(self, experiment: Experiment):
        super().__init__()
        self._experiment = experiment

    @Slot()
    def run(self):
        try:
            result = self._experiment.scan()
        except Exception as e:  # report any scan failure to the GUI
            _logger.exception("Error during scan")
            self.failed.emit(str(e))
            return
        self.finished.emit(result)


class _ScanRunner(QObject):
    """
    Owns the progress dialog and the worker thread for a single `scan()` run.

    Created on the GUI thread (from `Experiment.execute()`), so its slots
    below always run on the GUI thread - even though `_ScanWorker.progress`
    is emitted from the background thread - because Qt automatically
    delivers cross-thread signal/slot connections via a queued connection
    based on the *receiver's* thread affinity.

    """

    def __init__(self, experiment: Experiment):
        super().__init__()
        self.experiment = experiment
        self.result = None
        self.error: str | None = None

        self.dialog = QProgressDialog(
            "Starting...", "Abort", 0, 1, experiment.main_window
        )
        self.dialog.setWindowTitle(experiment.name)
        self.dialog.setMinimumDuration(0)
        self.dialog.setAutoClose(False)
        self.dialog.setAutoReset(False)
        self.dialog.canceled.connect(self._on_cancel)

        self.thread = QThread()
        self.worker = _ScanWorker(experiment)
        self.worker.moveToThread(self.thread)

        # Let `Experiment.report_progress()` reach this worker's signal.
        experiment._worker = self.worker

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

    def run(self):
        """
        Start the worker thread and block (while still processing GUI
        events, so the progress dialog stays responsive) until it finishes.

        """
        loop = QEventLoop()
        self.thread.finished.connect(loop.quit)
        self.thread.start()
        loop.exec()
        self.thread.wait()
        self.dialog.close()
        return self.result

    @Slot()
    def _on_cancel(self):
        self.experiment._cancel_requested = True

    @Slot(int, int, str)
    def _on_progress(self, current: int, total: int, text: str):
        if self.dialog.maximum() != total:
            self.dialog.setMaximum(total)
        self.dialog.setValue(current)
        if text:
            self.dialog.setLabelText(text)

    @Slot(object)
    def _on_finished(self, result):
        self.result = result

    @Slot(str)
    def _on_failed(self, message: str):
        self.error = message


class Experiment(ABC):
    """
    Experiment class used to define experiments.

    More specifically, it allows to define sequences of communications to the devices.
    The GUI runs a selected experiment by `Experiment.execute()`

    `Experiment.execute()` handles the generation of a valid datafolder,
    starts a logger,
    runs a scan that must be defined in a specific `<experiment>.py` file
    on a background thread (so the GUI stays responsive),
    and allows the user to provide a final comment to be logged.

    """
    # Has to be defined manually
    name: str = ""
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

        # Progress / threading state, populated by `execute()` / `_ScanRunner`
        self._worker: _ScanWorker | None = None
        self._cancel_requested: bool = False
        self.result = None

    @property
    def all_parameters(self) -> tuple[type[Parameter], ...]:
        """
        Collection of base parameters (name, comment) and experiment-specific parameters.

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

    def get_parameters(self) -> dict:
        """
        Get the experiment parameters from the main window

        Returns
        -------
        exp_settings: dict
            Settings from the experimental subpanel
        
        """
        main_window = self.main_window

        settings = main_window.get_all_settings()
        exp_settings = settings["experiment"]
        return exp_settings

    def report_progress(
        self,
        current: int,
        total: int,
        start_time: float | None = None,
        extra: str = "",
    ) -> bool:
        """
        Report scan progress and check for a cancellation request.

        Call this periodically from within `scan()` - which runs on a
        background thread - to keep the GUI's progress dialog in sync.
        Handles building a standard progress label (optionally including
        elapsed/estimated-remaining time) so individual experiments don't
        need to format or display anything themselves.

        Parameters
        ----------
        current: int
            Number of steps completed so far.
        total: int
            Total number of steps.
        start_time: float, optional
            `time.time()` value from when the scan started. When given, the
            progress label includes elapsed and estimated remaining time.
        extra: str, optional
            Extra text appended to the progress label, e.g. a live readout.

        Returns
        -------
        canceled: bool
            True if the user clicked "Abort" (or cancellation was otherwise
            requested). `scan()` should treat this as a request to stop and
            return whatever results it has so far - it is *not* raised as
            an exception, so the experiment stays in control of cleanup and
            partial results.

        """
        text = f"Completed: {current}/{total}"
        if start_time is not None:
            elapsed = time.time() - start_time
            rate = elapsed / current if current else 0.0
            remaining = rate * (total - current)
            text += (
                f"\nElapsed time: {time.strftime('%M min %S s', time.gmtime(elapsed))}"
                f"\nEstimated remaining time: {time.strftime('%M min %S s', time.gmtime(remaining))}"
            )
        if extra:
            text += f"\n{extra}"

        if self._worker is not None:
            self._worker.progress.emit(current, total, text)

        return self._cancel_requested

    @abstractmethod
    def scan(self):
        """
        Every experiment should be defined by a `scan` function.

        So, when you define a new experiment,
        the `<experiment>.py` file should contain an `Experiment` class
        with a defined `scan` function.

        `scan()` runs on a background thread. Use `self.get_parameters()`
        to read the experiment's settings, and call
        `self.report_progress(current, total, ...)` periodically to update
        the progress dialog and check whether the user requested a cancel.

        """
        raise NotImplementedError

    # Set up Logbook
    @contextmanager
    def _file_logging(self, log_path: Path):
        """
        Start a new logbook for the experiment.

        Adds a handler to the main logger (`logging.getlogger(__name__)`)
        that writes all logs up to the `INFO` level to the logbook.

        Before adding the handler,
        the user comment is logged.

        Upon finishing the experiment,
        the handler is removed and closed.

        Parameter
        ---------
        log_path: Path
            targeted file location for the logbook

        """
        # Write settings from the GUI as a plain header
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Settings ===\n")
            f.write(json.dumps(self.settings, indent=2, default=str))
            f.write("\n=== Log ===\n")

        handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        _logger.addHandler(handler)
        try:
            yield                          
        finally:
            _logger.removeHandler(handler)
            handler.close()

    def execute(self):
        """
        The code that runs when an experiment is initiated from the GUI.

        It handles:
        * Preparation of the data folder
        * Initiating the logger for the logbook of the experiment
        * Validating the required devices
        * Running the `scan` on a background thread, with a shared
          progress dialog that stays responsive and cancelable
        * Adding a final comment to the logbook

        """
        # Prepare data folder
        try:
            self.data_folder = data_folder(self.main_window)
        except OSError as e:
            _logger.exception("OS Error")
            QMessageBox.warning(self.main_window, "OS Error", str(e))
            return
        self.filename = file_name(self.data_folder, self.settings["experiment"]["title"])

        # Intiate and Maintain Logbook
        save_production_settings(self.data_folder, self.filename, self.settings)
        with self._file_logging(self.data_folder / f"{self.filename}_log.txt"):

            # Validate devices
            try:
                self.validate_devices()
            except (OSError, RuntimeError) as e:
                _logger.exception("Device Error")
                QMessageBox.warning(self.main_window, "Device Error", str(e))
                return

            # Run Scan on a background thread
            _logger.info("Scan started")

            with ExitStack() as stack:
                self.devices = {}
                dm = get_device_manager()

                try:
                    for key in self.required_devices:
                        self.devices[key] = stack.enter_context(dm.reserve(key))
                except RuntimeError as e:
                    _logger.exception("Device Reservation Error")
                    QMessageBox.warning(self.main_window, "Device Busy", str(e))
                    return
            
                self._cancel_requested = False

                runner = _ScanRunner(self)
                self.result = runner.run()

                self._worker = None

                if runner.error is not None:
                    _logger.error("Scan failed: %s", runner.error)
                    QMessageBox.warning(self.main_window, "Scan Error", runner.error)
                    return
                else:
                    _logger.info("Scan completed.")

            # Final comment
            comment_box = CommentBox(self.main_window)
            if comment_box.exec() == QDialog.Accepted:
                comment = comment_box.get_comment()
                with open(self.data_folder / f"{self.filename}_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n=== Final comment ===\n{comment}\n")


# ===================
# Registry
# ===================
EXPERIMENT_REGISTRY: dict[str, type[Experiment]] = {}


def register_experiment(experiment: type[Experiment]) -> type[Experiment]:
    if experiment.name in EXPERIMENT_REGISTRY:
        raise ValueError(f"Duplicate experiment name: {experiment.name}")
    EXPERIMENT_REGISTRY[experiment.name] = experiment
    return experiment
