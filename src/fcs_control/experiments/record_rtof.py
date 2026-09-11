import time

from ..devices import get_device_manager
from .base import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10

@register_experiment
class Record_RTOF(Experiment):
    name = "Record RTOF"
    description = "Records the RTOF mass spectrum over a chosen amount of cycles."
    required_devices = ('primaryscope')

    parameters = (
        Parameter('num', 'Number of Cycles', 'int', 0),
    )

    def scan(self):
        start_time = time.time()
        parameters = self.get_parameters()
        num = parameters['num']
        dm = get_device_manager()
        datasum = None

        for i in range(num):
            if self.report_progress(i, num, start_time):
                self.running = False
                break

            # Read scope
            time.sleep(_SCOPE_AVERAGES / _FREQUENCY)    # Wait until scope averaging is fully refreshed
            data = dm.primaryscope.read()

            # Collect Data
            if datasum is None:
                datasum = data[:, 1].copy()
            else:
                datasum += data[:, 1]

        return datasum