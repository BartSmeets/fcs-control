import logging
import time

from ..experiments import Experiment, Parameter, register_experiment

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
        start_time = time.time()
        parameters = self.get_parameters()

        num = parameters['num']
        short = parameters['short_text']
        long = parameters['long_text']

        extra = (f"short text: {short}\n"
                 f"long text: {long}")

        for i in range(num):
            if self.report_progress(i, num - 1, start_time, extra):
                self.running = False
                break

            time.sleep(0.05)
