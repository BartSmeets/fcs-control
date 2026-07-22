import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal


def setup_logging():

    Path("logs").mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.WARNING,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                "logs/app.log",
                encoding="utf-8"
            ),
            logging.StreamHandler(),
        ],
    )


class LogEmitter(QObject):
    log_message = Signal(str)


class QTextEditHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()

    def emit(self, record):
        msg = self.format(record)
        self.emitter.log_message.emit(msg)
