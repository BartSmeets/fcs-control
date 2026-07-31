from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
)

_CONNECTED_GENERATORS = ['Quantum 9520', 'Stanford DG535']
_AVAILABLE_CHANNELS = {
    'Quantum 9520': ["A", "B", "C", "D", "E", "F", "G", "H"],
    'Stanford DG535': ["A", "B", "C", "D"],
}


class DelayPanel(QGroupBox):
    def __init__(self, device_manager, parent=None):
        super().__init__('Delays', parent)

        layout = QHBoxLayout(self)
        self.boxes = {}
        for generator in _CONNECTED_GENERATORS:
            box = _DelayGenBox(generator)

            self.boxes[generator] = box
            layout.addWidget(box)

    def get_settings(self):
        return {
            generator: box.get_settings() for generator, box in self.boxes.items()
        }


class _DelayGenBox(QGroupBox):
    def __init__(self, generator, parent=None):
        super().__init__(generator, parent)

        self.channels = _AVAILABLE_CHANNELS[generator]

        self.delays = {}
        self.refs = {}

        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 0)

        # Header row
        layout.addWidget(QLabel("<b>Channel</b>"), 0, 0)
        layout.addWidget(QLabel("<b>Delay (μs)</b>"), 0, 1)
        layout.addWidget(QLabel("<b>Reference</b>"), 0, 2)

        for row, ch in enumerate(self.channels, start=1):
            # Column 1: channel label
            layout.addWidget(QLabel(ch), row, 0)

            # Column 2: delay value input
            delay_spin = QDoubleSpinBox()
            delay_spin.setRange(-1e6, 1e6)
            delay_spin.setDecimals(1)
            delay_spin.setSingleStep(0.1)
            layout.addWidget(delay_spin, row, 1)
            self.delays[ch] = delay_spin

            # Column 3: reference channel selection
            ref_combo = QComboBox()
            ref_combo.addItem("T0")
            ref_combo.addItems([c for c in self.channels if c != ch])
            layout.addWidget(ref_combo, row, 2)
            self.refs[ch] = ref_combo

        self.setLayout(layout)

    def get_settings(self):
        """Return {channel: (delay_value, reference_channel)}"""
        return {
            ch: {'delay': self.delays[ch].value(), 
                 'reference': self.refs[ch].currentText()}
            for ch in self.channels
        }
            