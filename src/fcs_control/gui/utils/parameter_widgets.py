"""
Build the widgets to provide the experiment specific parameters.

"""

from PySide6.QtWidgets import QLineEdit, QSpinBox, QTextEdit, QWidget

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
    spinbox.value = int(p.default)
    spinbox.minimum = p.minimum
    spinbox.maximum = p.maximum
    return spinbox


# ========================================
#           BUILDERS and READERS
#   dicts for specific types of parameters
# ========================================
_BUILDERS = {
    'short_text': _build_linetext,
    'long_text': _build_text,
    'int': _build_int,
    }

_READERS = {
    "short_text": lambda widget: widget.text(),
    "long_text": lambda widget: widget.toPlainText(),
    "int": lambda widget: widget.value(),
    }
