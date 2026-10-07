"""
Progress tracking and cancellation for experiments.

This module has no Qt dependency. `ProgressTracker` is driven from the
scan thread and hands finished progress updates to a callback (`on_update`),
which the scan runner connects to the GUI.

Contains
--------
ProgressTracker: Class
    Nestable progress reporting, time estimation and cancellation
PROGRESS_SCALE: int
    The progress bar always runs from 0 to this value

"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")

PROGRESS_SCALE = 1000


def format_duration(seconds: float) -> str:
    """Format seconds as `MM min SS s` (or `H h MM min SS s` above an hour)."""
    minutes, secs = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} h {minutes:02d} min {secs:02d} s"
    return f"{minutes} min {secs:02d} s"


class _Estimator:
    """
    Estimates the remaining time by blending an a-priori total duration
    with the measured pace.

    The prior fades out as the completed fraction `f` grows:

        c = f / (f + f0)
        total = (1 - c) * prior + c * (elapsed / f)

    So an instant first step does not break the estimate, and the real
    clock takes over as the scan progresses. Without a prior it is a plain
    extrapolation of the measured pace.

    """

    def __init__(self, prior_total: float | None = None, f0: float = 0.1):
        self.prior_total = prior_total
        self.f0 = f0
        self.start = time.monotonic()

    def elapsed(self) -> float:
        return time.monotonic() - self.start

    def remaining(self, fraction: float) -> float | None:
        """Remaining seconds, or None if there is nothing to base it on yet."""
        if fraction >= 1:
            return 0.0
        if fraction <= 0:
            return self.prior_total
        measured_total = self.elapsed() / fraction
        if self.prior_total is None:
            total = measured_total
        else:
            weight = fraction / (fraction + self.f0)
            total = (1 - weight) * self.prior_total + weight * measured_total
        return total * (1 - fraction)


@dataclass
class _Frame:
    """State of one active `track()` loop."""
    total: int
    extra: str | Callable[[Any], str]
    done: int = 0
    item: Any = None


class ProgressTracker:
    """
    Tracks progress of nested loops as one fraction, and handles cancellation.

    Attributes
    ----------
    on_update: Callable[[int, str], None] | None
        Called with `(value, label)` on every progress change, where `value`
        runs from 0 to `PROGRESS_SCALE`. Called from the scan thread.

    """

    def __init__(self):
        self.on_update: Callable[[int, str], None] | None = None
        self._cancel = threading.Event()   # thread-safe, unlike a plain bool
        self._frames: list[_Frame] = []
        self._estimator: _Estimator | None = None

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------
    def reset(self):
        """Prepare for a new scan."""
        self._cancel.clear()
        self._frames.clear()
        self._estimator = None

    def request_cancel(self):
        """Ask the running scan to stop. Safe to call from any thread."""
        self._cancel.set()

    @property
    def cancel_requested(self) -> bool:
        return self._cancel.is_set()

    def sleep(self, seconds: float):
        """Sleep that returns early when a cancel is requested."""
        self._cancel.wait(seconds)

    # ------------------------------------------------------------------
    # Tracking
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
        Iterate over `iterable` while reporting progress. Can be nested.

        The iteration stops cleanly (no exception) once a cancel is requested.
        Loops started after a cancel yield nothing.

        Parameters
        ----------
        iterable
            Anything iterable.
        total: int, optional
            Number of items. Defaults to `len(iterable)`; required for generators.
        step_time: float, optional
            Expected seconds per item of this loop, including everything nested
            in it. Only used on the outermost loop, where it seeds the time estimate.
        extra: str or callable(item) -> str, optional
            Text shown in the progress dialog while this loop is active.

        """
        if total is None:
            total = len(iterable)  # type: ignore[arg-type]
        if not self._frames:
            prior = step_time * total if step_time else None
            self._estimator = _Estimator(prior)

        frame = _Frame(total=max(total, 1), extra=extra)
        self._frames.append(frame)
        try:
            for item in iterable:
                if self.cancel_requested:
                    return
                frame.item = item
                self._publish()
                yield item
                frame.done += 1
                self._publish()
        finally:
            self._frames.remove(frame)

    def _fraction(self) -> float:
        """Overall completed fraction across all nested loops."""
        fraction, scale = 0.0, 1.0
        for frame in self._frames:          # outer -> inner
            fraction += scale * frame.done / frame.total
            scale /= frame.total
        return min(fraction, 1.0)

    def _publish(self):
        if self.on_update is None or self._estimator is None:
            return
        fraction = self._fraction()
        remaining = self._estimator.remaining(fraction)

        lines = [
            f"Elapsed time: {format_duration(self._estimator.elapsed())}",
            "Estimated remaining time: "
            + (format_duration(remaining) if remaining is not None else "estimating..."),
        ]
        for frame in self._frames:          # outer -> inner
            extra = frame.extra(frame.item) if callable(frame.extra) else frame.extra
            if extra:
                lines.append(extra)

        self.on_update(int(fraction * PROGRESS_SCALE), "\n".join(lines))
