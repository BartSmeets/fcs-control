"""
Build the widgets to provide the experiment specific parameters.

"""

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QWidget,
)

from ...experiments import Parameter


def build_widget(param: Parameter) -> QWidget:
    """
    Builds the widget for a given Parameter

    """
    try:
        builder = _BUILDERS[param.type]
    except KeyError:
        raise ValueError(f"No widget for type: {param.type}")
    return builder(param)

def get_value(param: Parameter, widget: QWidget):
    """
    Reads the value of a given parameters from the user widget
    
    """
    try:
        reader = _READERS[param.type]
    except KeyError:
        raise ValueError(f"No widget for type: {param.type}")
    return reader(widget)

def _build_linetext(p: Parameter) -> QLineEdit:
    """
    Build widget for text on a single line

    """
    textbox = QLineEdit()
    textbox.setText(str(p.default))
    return textbox

def _build_text(p: Parameter) -> QTextEdit:
    """
    Build widget for text in a textbox
    
    """
    textbox = QTextEdit()
    textbox.setText(str(p.default))
    return textbox

def _build_int(p: Parameter) -> QSpinBox:
    """
    Build widget for an integer input
    
    """
    spinbox = QSpinBox()
    spinbox.setValue = int(p.default)
    spinbox.setMinimum(int(p.minimum))
    spinbox.setMaximum(int(p.maximum))

    return spinbox

def _build_float(p: Parameter) -> QDoubleSpinBox:
    """
    Build widget for a floating input

    """
    spinbox = QDoubleSpinBox()
    spinbox.setValue = float(p.default)
    spinbox.setMinimum(float(p.minimum))
    spinbox.setMaximum(float(p.maximum))
    spinbox.setDecimals(int(p.decimals))

    return spinbox

def _build_option(p: Parameter) -> QComboBox:
    combobox = QComboBox()
    combobox.addItems(p.options)
    return combobox

# ========================================
#           BUILDERS and READERS
#   dicts for specific types of parameters
# ========================================
_BUILDERS = {
    'short_text': _build_linetext,
    'long_text': _build_text,
    'int': _build_int,
    'float': _build_float,
    'option': _build_option,
    }

_READERS = {
    "short_text": lambda widget: widget.text(),
    "long_text": lambda widget: widget.toPlainText(),
    "int": lambda widget: widget.value(),
    "float": lambda widget: widget.value(),
    "option": lambda widget: widget.currentText(),
    }
