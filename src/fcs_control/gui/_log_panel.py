import logging

from PySide6.QtWidgets import QPlainTextEdit

from fcs_control.utils.logging import QTextEditHandler


class LogPanel(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

        # Logging setup
        self.log_handler = QTextEditHandler()

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        self.log_handler.setFormatter(formatter)

        self.log_handler.emitter.log_message.connect(
            self.append_log
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.log_handler)

    def append_log(self, text):
            self.appendPlainText(text)