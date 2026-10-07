"""
Runs a scan on a background thread behind a progress dialog.

Contains
--------
ScanRunner: Class
    Owns the progress dialog and the worker thread for a single scan

"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QProgressDialog, QWidget

from fcs_control.experiments._progress import PROGRESS_SCALE, ProgressTracker

_logger = logging.getLogger(__name__)

_REFRESH_MS = 1000   # how often the time labels are refreshed


class _ScanWorker(QObject):
    """
    Calls `scan()` on a background thread.

    Lives on a `QThread` (via `moveToThread`), so everything inside `run()`
    executes off the GUI thread. Communicates back exclusively via signals.

    """
    progress = Signal(int, str)   # value (0..PROGRESS_SCALE), label text
    finished = Signal(object)     # scan() return value
    failed = Signal(str)          # str(exception)

    def __init__(self, scan: Callable[[], Any]):
        super().__init__()
        self._scan = scan

    @Slot()
    def run(self):
        try:
            result = self._scan()
        except Exception as e:  # report any scan failure to the GUI
            _logger.exception("Error during scan")
            self.failed.emit(str(e))
            return
        self.finished.emit(result)


class ScanRunner(QObject):
    """
    Owns the progress dialog and the worker thread for a single scan.

    Create it on the GUI thread. Its slots then run on the GUI thread, even
    though the worker's signals are emitted from the background thread: Qt
    delivers cross-thread connections as queued calls, based on the
    *receiver's* thread affinity.

    Parameters
    ----------
    scan: callable
        The function to run on the background thread.
    tracker: ProgressTracker
        Receives the abort request and delivers progress updates.
    title: str
        Window title of the progress dialog.
    parent: QWidget, optional
        Parent window of the progress dialog.

    Attributes
    ----------
    result
        Return value of `scan()`, available after `run()`.
    error: str | None
        Message of the exception that ended the scan, if any.

    """

    def __init__(
        self,
        scan: Callable[[], Any],
        tracker: ProgressTracker,
        title: str,
        parent: QWidget | None = None,
    ):
        super().__init__()
        self._tracker = tracker
        self.result: Any = None
        self.error: str | None = None

        self._dialog = QProgressDialog("Starting...", "Abort", 0, PROGRESS_SCALE, parent)
        self._dialog.setWindowTitle(title)
        self._dialog.setMinimumDuration(0)
        self._dialog.setAutoClose(False)
        self._dialog.setAutoReset(False)
        self._dialog.canceled.connect(self._on_cancel)

        # Keeps the elapsed/remaining time moving while a long step is running
        self._ticker = QTimer(self)
        self._ticker.setInterval(_REFRESH_MS)
        self._ticker.timeout.connect(self._on_tick)

        self._thread = QThread()
        self._worker = _ScanWorker(scan)
        self._worker.moveToThread(self._thread)

        tracker.on_update = self._worker.progress.emit

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)

    def run(self):
        """
        Start the worker thread and block until it finishes, while still
        processing GUI events so the progress dialog stays responsive.

        """
        loop = QEventLoop()
        self._thread.finished.connect(loop.quit)
        self._thread.start()
        self._ticker.start()
        loop.exec()
        self._ticker.stop()
        self._thread.wait()

        # Closing the dialog emits `canceled`, which is not a user abort.
        self._dialog.canceled.disconnect(self._on_cancel)
        self._dialog.close()
        self._dialog.deleteLater()
        self._tracker.on_update = None
        return self.result

    @Slot()
    def _on_cancel(self):
        _logger.info("Abort requested")
        self._ticker.stop()     # the dialog is hidden by the abort; do not keep updating it
        self._tracker.request_cancel()

    @Slot()
    def _on_tick(self):
        update = self._tracker.render()
        if update is not None:
            self._on_progress(*update)

    @Slot(int, str)
    def _on_progress(self, value: int, text: str):
        self._dialog.setValue(value)
        self._dialog.setLabelText(text)

    @Slot(object)
    def _on_finished(self, result: Any):
        self.result = result

    @Slot(str)
    def _on_failed(self, message: str):
        self.error = message
