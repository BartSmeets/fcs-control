import numpy as np

from fcs_control.experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10
_STEP_TIME = _SCOPE_AVERAGES / _FREQUENCY

@register_experiment
class Record_RTOF(Experiment):
    name = "Record RTOF"
    description = "Records the RTOF mass spectrum over a chosen amount of cycles."
    required_devices = ('primaryscope',)

    parameters = (
        Parameter('num', 'Number of Cycles', 'int', 0),
    )

    def scan(self):
        parameters = self.get_parameters()

        num = parameters['num']
        scope = self.devices['primaryscope']

        datasum = None
        
        for _ in self.track(range(num), step_time=_STEP_TIME, extra=lambda j: f"Cycle: {j+1}/{num}"):

            # Read scope
            self.sleep(_SCOPE_AVERAGES / _FREQUENCY)    # Wait until scope averaging is fully refreshed
            data = scope.read('CH1')
            if datasum is None:
                datasum = data
            else:
                datasum[:, 1] += data[:, 1]

        if datasum is None:
            return None

        np.save(self.data_folder / f"{self.filename}.npy", datasum)
        return datasum