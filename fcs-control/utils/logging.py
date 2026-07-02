import logging
from pathlib import Path


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
