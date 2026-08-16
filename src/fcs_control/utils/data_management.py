import json
import logging
import os
from datetime import date
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from ..config import NETWORK

_logger = logging.getLogger(__name__)


def data_folder(parent_window = None):
    """
    Set the folder to store the data and logs.

    """
    # What's the date please?
    today = date.today()  # noqa: DTZ011

    # Retrieve data location
    base = Path(NETWORK.data_folder)
    while not os.path.exists(base):
        _logger.warning(f"Cannot connect to {base}. Is the PC offline by any chance?")

        answer = QMessageBox.question(parent_window, 
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

    _logger.info(f"Using experiment folder: {day_folder}")
    return day_folder


def file_name(data_folder: Path, title: str) -> str:
    """
    Determine filename: add a counter if file already exists

    Parameters
    ----------
    data_folder: Path
        Only used for checking if already exists
    title: str
        Short name for the scan

    Returns
    -------
    filename: str
        Filename that mirrors `title`, but with a suffix if that title already existed

    """
    today = date.today()  # noqa: DTZ011
    prefix = f"{today.strftime("%d%m")}_{title}"
    counter = 0
    while True:
        suffix = f"_{counter}" if counter else ""
        filename = f"{prefix}{suffix}"
        if not (data_folder / f"{filename}_log.txt"):
            break
        counter += 1
    return filename


def save_production_settings(folder: Path, filename: str, settings: dict):
    """
    Save production settings to a material specific folder:

    ``.\\Production_Settings_Only\\MainMaterial\\MaterialList``
    
    """
    settings_folder = folder / "Production_Settings_Only"

    # Create folder for main material
    main_material = settings["materials"][0]
    settings_folder = settings_folder / str(main_material)
    settings_folder.mkdir(exist_ok = True)

    # Create subfolder for multiple materials
    material_list = settings["materials"]
    if len(material_list) > 1:
        settings_folder = settings_folder / str(material_list)
    else:
        settings_folder = settings_folder / f"pure_{main_material}"
    settings_folder.mkdir(exist_ok=True)

    with open(settings_folder / f"{filename}_settings.txt", "w", encoding="utf-8") as f:
        f.write("=== Settings ===\n")
        f.write(json.dumps(settings, indent=2, default=str))
