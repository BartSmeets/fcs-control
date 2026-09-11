import logging
import time

from .base import Experiment, register_experiment

_logger = logging.getLogger(__name__)


@register_experiment
class Test(Experiment):
    name = "Test"
    description = "Nothing here. Just for testing"
    required_devices = ()

    def scan(self):
        start_time = time.time()

        for i in range(101):
            if self.report_progress(i, 100, start_time):
                self.running = False
                break

            time.sleep(0.05)
