import logging
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

_CONNECTED_GENERATORS = ['Quantum 9520', 'Stanford DG535']
_AVAILABLE_CHANNELS = {
    'Quantum 9520': ["A", "B", "C", "D", "E", "F", "G", "H"],
    'Stanford DG535': ["A", "B", "C", "D"],
}

_logger = logging.getLogger(__name__)


class DelayPanel(QGroupBox):
    def __init__(self, device_manager, parent=None):
        super().__init__('Delays', parent)

        layout = QHBoxLayout(self)
        self.boxes = {}
        for name in _CONNECTED_GENERATORS:
            box = _DelayGenBox(name, device_manager)

            self.boxes[name] = box
            layout.addWidget(box)

    def get_settings(self):
        return {
            name: box.get_settings() for name, box in self.boxes.items()
        }

@dataclass
class _ChannelWidgets:
    delay: QDoubleSpinBox
    ref: QComboBox

class _DelayGenBox(QGroupBox):
    def __init__(self, name, device_manager, parent=None):
        super().__init__(name, parent)

        self.device_manager = device_manager
        self.name = name
        self.channels = _AVAILABLE_CHANNELS[name]

        self.delays = {}
        self.refs = {}

        self._build_ui()
        self.refresh_from_device()

    def _build_ui(self):
        self.channels_widgets = {}

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

            # Column 3: reference channel selection
            ref_combo = QComboBox()
            ref_combo.addItem("T0")
            ref_combo.addItems([c for c in self.channels if c != ch])
            layout.addWidget(ref_combo, row, 2)

            self.channels_widgets[ch] = _ChannelWidgets(delay=delay_spin, ref=ref_combo)

        self.setLayout(layout)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_from_device)
        layout.addWidget(refresh_btn, layout.rowCount(), 0, 1, 3)

    def refresh_from_device(self):
        if self.name == 'Quantum 9520':
            device = self.device_manager.quantum
        elif self.name == 'Stanford DG535':
            _logger.warning(f"{self.name} refresh not yet implemented")
            return
        else:
            raise ValueError(f"Unknown generator: {self.name}")

        if device is None:
            _logger.warning(f"{self.name} is not connected.")
            return

        for channel, widgets in self.channels_widgets.items():
            widgets.delay.blockSignals(True)
            widgets.delay.setValue(device.get_delay(channel))
            widgets.delay.blockSignals(False)

            widgets.ref.blockSignals(True)
            ref_channel = device.get_reference(channel)
            idx = widgets.ref.findText(ref_channel)
            if idx >= 0:
                widgets.ref.setCurrentIndex(idx)
            widgets.ref.blockSignals(False)

    def get_settings(self):
        """Return {channel: (delay_value, reference_channel)}"""
        return {
            ch: {'delay': self.delays[ch].value(), 
                 'reference': self.refs[ch].currentText()}
            for ch in self.channels
        }
            