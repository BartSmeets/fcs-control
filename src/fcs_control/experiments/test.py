import logging

from fcs_control.experiments import Experiment, Parameter, register_experiment

_logger = logging.getLogger(__name__)


@register_experiment
class Test(Experiment):
    name = "Test"
    description = "Nothing here. Just for testing"
    required_devices = ()
    parameters = (
        Parameter('num', 'Number of Cycles', 'int', 0),
        Parameter('short_text', 'Short Text Test', 'short_text', 'test'),
        Parameter('long_text', 'Long Text Test', 'long_text', 'test'),
        )

    def scan(self):
        parameters = self.get_parameters()

        num = parameters['num']
        short = parameters['short_text']
        long = parameters['long_text']

        extra = lambda j: (f"Cycle: {j+1}/{num}\n"
                           f"short text: {short}\n"
                           f"long text: {long}")

        for _ in self.track(range(num), step_time=0.05, extra=extra):
            self.sleep(0.05)
