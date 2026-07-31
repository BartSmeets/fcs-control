"""
Builds the panel for the delay generator.

"""
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

# ====================
# Registry: Add new delay generators and their available channels here
# ====================
_CONNECTED_GENERATORS  = {
    'Quantum 9520': ["A", "B", "C", "D", "E", "F", "G", "H"],
    'Stanford DG535': ["A", "B", "C", "D"],
}

_logger = logging.getLogger(__name__)


class DelayPanel(QGroupBox):
    """
    Main delay generator panel
    
    Methods
    -------
    get_settings: 
        returns settings dictionary.

    refresh: 
        refresh the panel values by reading from the devices
    
    """
    def __init__(self, device_manager, parent=None):
        super().__init__('Delays', parent)

        layout = QHBoxLayout(self)
        self.boxes = {}

        # Add BoxGroup for every generator in the registry
        for name in _CONNECTED_GENERATORS:
            box = _DelayGenBox(name, device_manager)

            self.boxes[name] = box
            layout.addWidget(box)

    def get_settings(self):
        """
        Returns
        ------- 
        settings dict:
            Keys: 
                names of the delay generators.

            Values:
                Setting_dict from that delay generator, 
                see `_DelayGenBox.get_settings()`
        
        """
        return {
            name: box.get_settings() for name, box in self.boxes.items()
        }

    def refresh(self):
        """
        Refreshes values by reading device

        See `_DelayGenBox.refresh()`
        
        """
        for box in self.boxes:
            box.refresh()


@dataclass
class _ChannelWidgets:
    """
    Class to collect settings per channel
    
    """
    delay: QDoubleSpinBox
    ref: QComboBox


class _DelayGenBox(QGroupBox):
    """
    Builds panel for individual delay generator

    Methods
    -------
    refresh: 
        refreshes values by reading device

    get_settings:
        returns settings dictionary.

    """
    def __init__(self, name, device_manager, parent=None):
        super().__init__(name, parent)

        # Common information
        self.device_manager = device_manager
        self.name = name
        self.channels = _CONNECTED_GENERATORS[name]

        # Dictionaries for storing input boxes
        self.delays = {}
        self.refs = {}

        # Build UI and initialise values
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """
        Build UI of panel
        
        """
        # Dictionary for storing channel widgets
        self.channels_widgets = {}

        # Layout configs
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 0)

        # Header row
        layout.addWidget(QLabel("<b>Channel</b>"), 0, 0)
        layout.addWidget(QLabel("<b>Delay (μs)</b>"), 0, 1)
        layout.addWidget(QLabel("<b>Reference</b>"), 0, 2)

        # Input widgets for every channel
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

            # Store widgets
            self.channels_widgets[ch] = _ChannelWidgets(delay=delay_spin, ref=ref_combo)
        # Commit Layout
        self.setLayout(layout)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn, layout.rowCount(), 0, 1, 3)

    def refresh(self):
        """
        Refreshes values of widgets by reading device
        
        """
        # Wire device
        if self.name == 'Quantum 9520':
            device = self.device_manager.quantum
        elif self.name == 'Stanford DG535':
            _logger.warning(f"{self.name} refresh not yet implemented") ## Not yet implemented!!
            return
        else:
            raise ValueError(f"Unknown generator: {self.name}")

        # Check if device is connected
        if device is None:
            _logger.warning(f"{self.name} is not connected.")
            return

        # Read device
        for channel, widgets in self.channels_widgets.items():
            # Read delay
            widgets.delay.blockSignals(True)
            widgets.delay.setValue(device.get_delay(channel))
            widgets.delay.blockSignals(False)

            # Read reference channel
            widgets.ref.blockSignals(True)
            ref_channel = device.get_reference(channel)
            idx = widgets.ref.findText(ref_channel)
            if idx >= 0:
                widgets.ref.setCurrentIndex(idx)
            widgets.ref.blockSignals(False)

    def get_settings(self):
        """
        Returns
        ------- 
        settings dict:
            Keys: 
                channel name (letter)
        
            Values:
                dict {'delay': delay value, 'reference': reference value} 
        
        """
        return {
            ch: {'delay': self.delays[ch].value(), 
                 'reference': self.refs[ch].currentText()}
            for ch in self.channels
        }
            