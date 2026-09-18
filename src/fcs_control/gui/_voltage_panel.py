"""
Builds VoltagePanel

"""
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ._material_panel import MaterialPanel


class VoltagePanel(QWidget):
    """
    VoltagePanel.

    Also includes misc settings.
    
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # TODO: read these from a defaults file
        self.voltages = ParameterGroup("Voltages", [
            # Observable, dtype, maximum, unit, default
            ("R1", int, 5000, "V", 0),
            ("R2", int, 5000, "V", 0),
            ("E1", int, 5000, "V", 0),
            ("E2", int, 5000, "V", 0),
            ("D1B", int, 1000, "V", 0),
            ("D2", int, 1000, "V", 0),
        ])
        layout.addWidget(self.voltages)

        self.materials = MaterialPanel(parent)
        layout.addWidget(self.materials)

        # TODO: read these from a defaults file
        self.misc = ParameterGroup("Misc", [
            # Observable, dtype, maximum, unit, default
            ("T", int, None, "K", 300),
            ("P", float, 11.0, "bar", 0),
            ("E laser", float, None, "mJ", 0),
            ("psv", float, 5.0, "kA", 0),
        ])
        layout.addWidget(self.misc)

        

    def get_settings(self) -> dict:
        """
        Settings of voltages, materials and misc

        """
        return {
            "voltages": self.voltages.get_settings(),
            "materials": self.materials.get_settings(),
            "misc": self.misc.get_settings(),
        }


class ParameterGroup(QGroupBox):
    """
    Parameter group to separate voltage from misc.

    Constructs the input boxes based on the parameters

    Parameters
    ----------
    title: str
        title of groupbox: voltage or misc
    parameters: list
        default settings

    """
    def __init__(self, title, parameters, parent=None):
        super().__init__(title, parent)

        layout = QFormLayout(self)
        self.spinboxes = {}

        # Construct the input boxes
        for name, dtype, maximum, unit, default in parameters:
            if dtype is float:
                box = QDoubleSpinBox()
                box.setDecimals(1)
                box.setMaximum(1e100)
            else:
                box = QSpinBox()
                box.setMaximum(2147483647)

            box.setFixedWidth(120)  # TODO: stylesheet or something

            if maximum is not None:
                box.setMaximum(maximum)
            box.setSuffix(f" {unit}")
            box.setValue(default)

            self.spinboxes[name] = box
            layout.addRow(f"{name} = ", box)

    def get_settings(self):
        """
        Returns
        -------
        dict[str, int | float]
            Keys are the voltage channels or name of the misc setting.
            Values are the values of their spinboxes
            
        """
        return {
            name: widget.value()
            for name, widget in self.spinboxes.items()
        }
