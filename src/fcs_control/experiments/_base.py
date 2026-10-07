"""
Defines the "rules" for defining experiments.

Contains
--------
Parameter: Class
    Class for communicating required parameters to the GUI
Experiment: Class
    Class for defining the Experiment
register_experiment: function
    Add the experiment to the REGISTRY

To define an experiment:
Add an experiment file `<experiment>.py`, containing an `Experiment` class
definition with the `@register_experiment` decorator:

```
@register_experiment
class Example(Experiment):
    name = 'example'
    description = 'This is an example'
    required_devices = ('some_device',)
    parameters = (Parameter('num', 'Number of Cycles', 'int', 0),)

    def scan(self):
        num = self.get_parameters()['num']
        for i in self.track(range(num), step_time=0.5):
            self.sleep(0.5)   # the work for one step
```

Progress reporting and abort handling are done by `self.track()`;
see `Experiment.track` for nesting and live read-outs.

"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from PySide6.QtWidgets import QDialog, QMessageBox

from fcs_control.devices import get_device_manager
from fcs_control.experiments._progress import ProgressTracker
from fcs_control.experiments._runner import ScanRunner
from fcs_control.gui.popup import CommentBox
from fcs_control.utils.data_management import (
    data_folder,
    file_name,
    save_production_settings,
)

if TYPE_CHECKING:
    from ..gui import MainWindow  # adjust relative path

T = TypeVar("T")

_logger = logging.getLogger(__name__)

# The logbook listens to the whole experiments package (and not just this
# module), so logs from every experiment file end up in it.
_PACKAGE_LOGGER = logging.getLogger("fcs_control.experiments")


@dataclass
class Parameter:
    """
    Parameter data class

    This class is used to communicate required parameters for an experiment to the GUI.

    Attributes
    ----------
    name: str
        Name of the parameter.
        More a tag or key, as it will be used to address the corresponding widget.
    label: str
        Label to show in the GUI
    type: ['int', 'float', 'short_text', 'long_text', 'option']
        Indicator for the type of widget that should be generated in the GUI
    default: Any
        Default value in the GUI
    minimum: float, default = 0
        Minimum numerical value (only used if applicable)
    maximum: float, default = 1e9
        Maximum numerical value (only used if applicable)
    decimals: int, default = 1
        Number of decimals for floating spinboxes
    options: list | None, default = None
        List of options to show in combobox
    step: float | None, default = None
        TODO: not implemented
    unit: str, default = ''
        TODO: not implemented

    """
    name: str
    label: str
    type: Literal['int', 'float', 'short_text', 'long_text', 'option']
    default: Any
    minimum: float = 0
    maximum: float = 1e9
    decimals: int = 1
    step: float | None = None
    unit: str = ""
    options: list[str] | None = None


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

    Attributes
    ----------
    name: str, default = ""
        name/key of the experiment
    description: str, default = ""
        Description of the experiment
        to be shown in the GUI
    required_devices: tuple[str, ...]
        Keys of the required devices
    parameters: tuple[Parameter, ...]
        Parameter settings
        for the widgets that should be generated in the GUI
    data_folder: Path | None
        Folder for data storage.
        Will be generated during run
    filename: str
        Base name for the data files. Will be generated during run
    devices: dict
        Reserved devices by key. Available inside `scan()`
    settings: dict
        Settings taken from the GUI panels
    result
        Return value of `scan()`

    Methods
    -------
    validate_devices
        Check if the required devices are connected
    get_parameters
        Read the experimental parameters
    track
        Iterate while reporting progress and handling aborts
    sleep
        Sleep that is interrupted by an abort
    cancel_requested
        Whether the user pressed "Abort"

    """
    # Has to be defined manually
    name: str = ""
    description: str = ""
    required_devices: tuple[str, ...] = ()
    parameters: tuple[Parameter, ...] = ()

    # Every experiment must have a title and comment
    _base_parameters: tuple[Parameter, ...] = (
        Parameter('title', 'File Name', 'short_text', ''),
        Parameter('comment', 'Babbelbox', 'long_text', ''),
    )

    # Will be generated during run
    data_folder: Path | None = None
    filename: str = ""

    def __init__(self, main_window: MainWindow | None = None):
        self.main_window = main_window
        self.settings: dict = {}
        self.devices: dict[str, Any] = {}
        self.result: Any = None
        self._ready = False
        self._progress = ProgressTracker()

        # Without a main window, the instance is only used for its metadata
        if main_window is None:
            return

        try:
            self.validate_devices()
        except (OSError, RuntimeError) as e:
            self._warn("Device Error", e)
            return

        main_window.delay_panel.refresh()
        self.settings = main_window.get_all_settings()
        self._ready = True

    @property
    def all_parameters(self) -> tuple[Parameter, ...]:
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

    def get_parameters(self) -> dict:
        """
        Get the experiment parameters

        These are the values from the moment the experiment was started.
        They are read from the snapshot taken in `__init__`, not from the
        widgets: `scan()` runs on a background thread, where Qt widgets must
        not be touched, and later edits in the GUI must not change a running
        scan (or make it differ from what the logbook says).

        Returns
        -------
        exp_settings: dict
            Copy of the settings from the experimental subpanel

        """
        return dict(self.settings["experiment"])

    # ------------------------------------------------------------------
    # Progress and abort handling (used inside `scan()`)
    # ------------------------------------------------------------------
    def track(
        self,
        iterable: Iterable[T],
        *,
        total: int | None = None,
        step_time: float | None = None,
        extra: str | Callable[[T], str] = "",
    ) -> Iterator[T]:
        """
        Iterate over `iterable` while reporting progress to the progress dialog.

        Handles the progress bar, the time estimate and the abort button.
        When the user aborts, the iteration simply ends (no exception), so
        the code after the loop still runs and can clean up or save partial
        results. Check `self.cancel_requested` afterwards where partial data
        must not be used.

        Loops can be nested; the bar shows the combined progress.

        ```
        for wavelength in self.track(waves, step_time=per_wavelength,
                                     extra=lambda wl: f"Wavelength: {wl:.1f} nm"):
            for _ in self.track(range(num)):
                ...
        ```

        Parameters
        ----------
        iterable
            Anything iterable.
        total: int, optional
            Number of items. Defaults to `len(iterable)`; required for generators.
        step_time: float, optional
            Expected seconds per item of this loop, including everything nested
            inside it. Only used on the outermost loop, where it seeds the time
            estimate until the measured pace takes over.
        extra: str or callable(item) -> str, optional
            Text shown in the progress dialog while this loop is active,
            e.g. a live read-out.

        """
        return self._progress.track(iterable, total=total, step_time=step_time, extra=extra)

    def sleep(self, seconds: float):
        """Sleep that returns early when the user aborts. Use instead of `time.sleep`."""
        self._progress.sleep(seconds)

    @property
    def cancel_requested(self) -> bool:
        """True once the user pressed "Abort"."""
        return self._progress.cancel_requested

    @abstractmethod
    def scan(self):
        """
        Every experiment should be defined by a `scan` function.

        So, when you define a new experiment,
        the `<experiment>.py` file should contain an `Experiment` class
        with a defined `scan` function.

        `scan()` runs on a background thread. Use `self.get_parameters()`
        to read the experiment's settings, and wrap the main loop(s) in
        `self.track(...)` to update the progress dialog and handle aborts.

        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Running an experiment
    # ------------------------------------------------------------------
    def execute(self):
        """
        The code that runs when an experiment is initiated from the GUI.

        It handles:
        * Preparation of the data folder
        * Initiating the logger for the logbook of the experiment
        * Reserving the required devices
        * Running the `scan` on a background thread, with a shared
          progress dialog that stays responsive and cancelable
        * Adding a final comment to the logbook

        """
        if not self._ready:
            return
        if not self._prepare_output():
            return

        with self._file_logging(self._log_path):
            with ExitStack() as stack:
                if not self._reserve_devices(stack):
                    return
                if not self._run_scan():
                    return
            self._ask_final_comment()

    @property
    def _log_path(self) -> Path:
        return self.data_folder / f"{self.filename}_log.txt"

    def _warn(self, title: str, error: Exception | str):
        """Log an error and show it to the user."""
        _logger.error("%s: %s", title, error, exc_info=isinstance(error, Exception))
        QMessageBox.warning(self.main_window, title, str(error))

    def _prepare_output(self) -> bool:
        """Create the data folder and file name, and store the production settings."""
        try:
            self.data_folder = data_folder(self.main_window)
        except OSError as e:
            self._warn("OS Error", e)
            return False
        self.filename = file_name(self.data_folder, self.settings["experiment"]["title"])
        save_production_settings(self.data_folder, self.filename, self.settings)
        return True

    def _reserve_devices(self, stack: ExitStack) -> bool:
        """Reserve all required devices; they are released when `stack` closes."""
        device_manager = get_device_manager()
        self.devices = {}
        try:
            for key in self.required_devices:
                self.devices[key] = stack.enter_context(device_manager.reserve(key))
        except RuntimeError as e:
            self._warn("Device Busy", e)
            return False
        return True

    def _run_scan(self) -> bool:
        """Run `scan()` on a background thread. Returns False if it failed."""
        self._progress.reset()
        _logger.info("Scan started")
        runner = ScanRunner(self.scan, self._progress, self.name, self.main_window)
        self.result = runner.run()

        if runner.error is not None:
            # The traceback was already logged by the worker
            _logger.error("Scan failed: %s", runner.error)
            QMessageBox.warning(self.main_window, "Scan Error", runner.error)
            return False

        _logger.info("Scan aborted by user." if self.cancel_requested else "Scan completed.")
        return True

    def _ask_final_comment(self):
        """Ask the user for a final comment and append it to the logbook."""
        comment_box = CommentBox(self.main_window)
        if comment_box.exec() == QDialog.Accepted:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== Final comment ===\n{comment_box.get_comment()}\n")

    @contextmanager
    def _file_logging(self, log_path: Path):
        """
        Start a new logbook for the experiment.

        Writes the GUI settings as a header, then adds a handler to the
        experiments package logger that writes all logs to the logbook.
        Upon finishing the experiment, the handler is removed and closed.

        Parameters
        ----------
        log_path: Path
            targeted file location for the logbook

        """
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Settings ===\n")
            f.write(json.dumps(self.settings, indent=2, default=str))
            f.write("\n=== Log ===\n")

        handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        _PACKAGE_LOGGER.addHandler(handler)
        try:
            yield
        finally:
            _PACKAGE_LOGGER.removeHandler(handler)
            handler.close()


# ===================
# Registry
# ===================
EXPERIMENT_REGISTRY: dict[str, type[Experiment]] = {}


def register_experiment(experiment: type[Experiment]) -> type[Experiment]:
    if experiment.name in EXPERIMENT_REGISTRY:
        raise ValueError(f"Duplicate experiment name: {experiment.name}")
    EXPERIMENT_REGISTRY[experiment.name] = experiment
    return experiment