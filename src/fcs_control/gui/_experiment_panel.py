"""
Build the experiment panel.

This file contains the main `ExperimentPanel` as well as the subpanel `ExperimentParameters`.

`ExperimentParameters` collects widgets from `utils.parameter_widgets` to build the input widgets for the experiment specific parameters.

"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
)

from ..experiments import EXPERIMENT_REGISTRY, Experiment, Parameter
from .utils.parameter_widgets import build_widget, get_value


class ExperimentPanel(QGroupBox):
    """
    Main Experiment Panel. 
    Combines the experiment selection, with the title and comment section, as well as the experiment dependent settings.
    
    To add an experiment, add them to ``EXPERIMENT_REGISTRY``, see ``..experiments``.
    
    DO NOT MAKE CHANGES HERE TO ADD AN EXPERIMENT!
    
    """
    def __init__(self, parent=None):
        super().__init__("Experiment", parent)
        
        self.exp_layout = QFormLayout(self)
        self.exp_layout.setAlignment(Qt.AlignTop)

        # Experiment Selection
        # Add a new experiment by adding it to the registry, see ..experiments
        self.experiment_combo = QComboBox(self)
        self.experiment_combo.addItems(list(EXPERIMENT_REGISTRY.keys()))
        self.experiment_combo.currentTextChanged.connect(self._on_experiment_change)

        # Experiment Widgets
        SelectedExperiment = EXPERIMENT_REGISTRY[self.experiment_combo.currentText()]
        self.experiment_widgets = _ExperimentParameters(SelectedExperiment)
        
        # Run Button
        self.run_btn = QPushButton("Run")
        self.run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.run_btn.clicked.connect(self._on_run)

        # Build Panel
        self.exp_layout.addRow("Experiment: ", self.experiment_combo)  
        self.exp_layout.addRow(self.experiment_widgets)
        self.exp_layout.addRow(self.run_btn)
        self.setLayout(self.exp_layout)

        self._on_experiment_change(self.experiment_combo.currentText())

    def _on_experiment_change(self, exp_name:str):
        """
        Update the experiment specific parameters.

        Settings are defined by the entries in ``EXPERIMENT_REGISTRY``, see ``..experiments``.

        """
        SelectedExperiment = EXPERIMENT_REGISTRY[exp_name]
        self.experiment_widgets.set_experiment(SelectedExperiment)

    def _on_run(self):
        """
        Activates on button press and executes the experiment.
        
        """
        SelectedExperiment = EXPERIMENT_REGISTRY[self.experiment_combo.currentText()]
        to_run = SelectedExperiment(main_window = self.window())
        to_run.execute()

    def get_settings(self):
        return self.experiment_widgets.get_parameters()


class _ExperimentParameters(QFormLayout):
    """
    Defines the sublayout where the user will provide the experiment specific parameters.
    
    """
    def __init__(self, experiment: type[Experiment], parent=None):
        super().__init__(parent)
        
        self._widgets: dict[str, object] = {}
        self._parameters: dict[str, Parameter] = {}
        self.set_experiment(experiment)

    def set_experiment(self, experiment: type[Experiment]) -> None:
        """
        Build and add the widgets
        
        """
        parameters = experiment().all_parameters
        description = experiment.description

        self._clear_rows()
        self.addRow(QLabel(f"Description: {description}"))      
        self.addItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))        
        for parameter in parameters:
            widget = build_widget(parameter)
            self._widgets[parameter.name] = widget
            self._parameters[parameter.name] = parameter
            self.addRow(f"{parameter.label}: ", widget)        

    def _clear_rows(self) -> None:
        """
        Clear the widgets.
        
        """
        while self.rowCount() > 0:
            self.removeRow(0)   
        self._widgets.clear()
        self._parameters.clear()

    def get_parameters(self) -> dict:
        """
        Get the values of the widgets

        The parameter information is neccessary because not every widget is read the same way...

        """
        return {
            name: get_value(parameter, self._widgets[name])
            for name, parameter in self._parameters.items()
        }