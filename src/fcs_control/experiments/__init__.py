import importlib
import pkgutil

from .base import EXPERIMENT_REGISTRY, Experiment, Parameter, register_experiment

__all__ = ["EXPERIMENT_REGISTRY", "Experiment", "Parameter", "register_experiment"]

_package_name = __name__
_skip = {"base", "__init__"}

# Import all experiment modules so they can register themselves.
for _, module_name, _ in pkgutil.iter_modules(__path__):
    if module_name not in _skip:
        importlib.import_module(f"{_package_name}.{module_name}")

del importlib, pkgutil, _package_name, _skip