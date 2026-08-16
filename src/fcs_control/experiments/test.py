from .base import Experiment, register_experiment


@register_experiment
class Test(Experiment):
    name = "Test"
    description = "Nothing here. Just for testing"
    required_devices = ()

    def scan(self):
        return 