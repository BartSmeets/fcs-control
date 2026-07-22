from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class voltagePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

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

        self.misc = ParameterGroup("Misc", [
            # Observable, dtype, maximum, unit, default
            ("T", int, None, "K", 300),
            ("P", float, 11.0, "bar", 0),
            ("E laser", float, None, "mJ", 0),
            ("psv", float, 5.0, "kA", 0),
        ])
        layout.addWidget(self.misc)

    def values(self):
        values = {}
        values.update(self.voltages.values())
        values.update(self.misc.values())
        return values


class ParameterGroup(QGroupBox):
    def __init__(self, title, parameters, parent=None):
        super().__init__(title, parent)

        layout = QFormLayout(self)
        self.spinboxes = {}

        for name, dtype, maximum, unit, default in parameters:
            if dtype is float:
                box = QDoubleSpinBox()
                box.setDecimals(1)
                box.setMaximum(1e100)
            else:
                box = QSpinBox()
                box.setMaximum(2147483647)

            if maximum is not None:
                box.setMaximum(maximum)
            box.setSuffix(f" {unit}")
            box.setValue(default)

            self.spinboxes[name] = box
            layout.addRow(f"{name} = ", box)

    def values(self):
        return {
            name: widget.value()
            for name, widget in self.spinboxes.items()
        }
