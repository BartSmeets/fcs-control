import time

import numpy as np

from ..experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10

@register_experiment
class Record_RTOF(Experiment):
    name = "Record RTOF"
    description = "Records the RTOF mass spectrum over a chosen amount of cycles."
    required_devices = ('primaryscope',)

    parameters = (
        Parameter('num', 'Number of Cycles', 'int', 0),
    )

    def scan(self):
        start_time = time.time()
        parameters = self.get_parameters()

        num = parameters['num']
        scope = self.devices['primaryscope']

        self.report_progress(0, num, start_time)
        datasum = scope.read('CH1')
        
        for i in range(1, num):
            if self.report_progress(i, num, start_time):
                break

            # Read scope
            time.sleep(_SCOPE_AVERAGES / _FREQUENCY)    # Wait until scope averaging is fully refreshed
            data = scope.read('CH1')
            datasum[:, 1] += data[:, 1]

        np.save(self.data_folder / f"{self.filename}.npy", datasum)
        return datasum