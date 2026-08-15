from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSizePolicy,
)

from ..devices import get_device_manager
from ..experiments import EXPERIMENT_REGISTRY, Experiment, Parameter


class ExperimentPanel(QGroupBox):
    """
    Main Experiment Panel. 
    Combines the experiment selection, with the title and comment section, as well as the experiment dependent settings.
    
    To add an experiment, add them to ``EXPERIMENT_REGISTRY``, see ``..experiments``.
    
    DO NOT MAKE CHANGES HERE TO ADD AN EXPERIMENT!
    
    """
    # Common Information
    device_manager = get_device_manager()
    active_experiment: type[Experiment] | None = None

    def __init__(self, parent=None):
        super().__init__("Experiment", parent)

        self.exp_layout = QFormLayout(self)
        self.exp_layout.setAlignment(Qt.AlignTop)

        # Experiment Selection
        # Add a new experiment by adding it to the registry, see ..experiments
        self.experiment_combo = QComboBox(self)
        self.experiment_combo.addItems(list(EXPERIMENT_REGISTRY.keys()))
        self.experiment_combo.currentTextChanged.connect(self._on_experiment_change)

        # Experiment Parameters
        experiment = EXPERIMENT_REGISTRY[self.experiment_combo.currentText()]
        self.parameters = experiment().all_parameters
        self.experiment_settings = _ExperimentParameters(self.parameters)

        # Run Button
        self.run_btn = QPushButton("Run")
        self.run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.run_btn.clicked.connect(self._on_run)

        # Build Panel
        self.exp_layout.addRow("Experiment: ", self.experiment_combo)
        self.exp_layout.addRow(self.experiment_settings)
        self.exp_layout.addRow(self.run_btn)
        self.setLayout(self.exp_layout)

        self._on_experiment_change(self.experiment_combo.currentText())

    def _on_experiment_change(self, exp_name:str):
        """
        Update the experiment specific parameters.

        Settings are defined by the entries in ``EXPERIMENT_REGISTRY``, see ``..experiments``.

        """
        experiment = EXPERIMENT_REGISTRY[self.experiment_combo.currentText()]
        self.parameters = experiment().all_parameters
        self.experiment_settings.set_experiment(self.parameters)

    def _on_run(self):
        """
        Activates on button press and executes the experiment.
        
        """
        to_run = self.active_experiment(main_window = self.window())
        to_run.execute(parameters = self.experiment_settings.get_parameters(to_run))


class _ExperimentParameters(QFormLayout):
    """
    Defines the sublayout where the user will provide the experiment specific parameters.
    
    """
    def __init__(self, parameters: tuple[type[Parameter], ...], parent=None):
        super().__init__(parent)
        self._widgets: dict[str, object] = {}   # Will store the information
        self.set_experiment(parameters)

    def set_experiment(self, parameters: tuple[type[Parameter], ...]) -> None:
        """
        Build and add the widgets
        
        """
        self._clear_rows()                              
        for parameter in parameters:
            widget = parameter.build_widget()
            self._widgets[parameter.name] = widget
            self.addRow(parameter.label, widget)        

    def _clear_rows(self) -> None:
        """
        Clear the widgets.
        
        """
        while self.rowCount() > 0:
            self.removeRow(0)   
        self._widgets.clear()

    def get_parameters(self, parameters: tuple[type[Parameter], ...]) -> dict:
        """
        Get the values of the widgets

        """
        return {
            parameter.name: parameter.get_value(self._widgets[parameter.name])
            for parameter in parameters
        }