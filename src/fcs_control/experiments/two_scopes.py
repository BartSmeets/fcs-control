import time

import numpy as np

from ..experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10

@register_experiment
class IR_scan(Experiment):
    name = "Both Scopes"
    description = (
        "This is a simple RTOF experiment that records both scopes."
    )
    required_devices = ('primaryscope', 
                        'secondaryscope',)

    parameters = (
            Parameter('num', 'Number of Cycles', 'int', 0),
        )

    def scan(self):
        start_time = time.time()
        primary_sum, secondary_sum = self._read_cycles(start_time)

        np.save(self.data_folder / f"{self.filename}_prime.npy", primary_sum)
        np.save(self.data_folder / f"{self.filename}_secon.npy", secondary_sum)

    def _read_cycles(self, start_time: float):
            """
            Read the requested number of cycles from the scopes.
            The parameters are only used for updating the progress bar.
    
            Parameters
            ----------
            start_time: float
                Start time of the full experiment

            Returns
            -------
            primary_sum: ndarray
                Array containing the summed data of the primary scope
            secondary_sum:
                Array containing the summed data of the primary scope
            
            """
            primary = self.devices['primaryscope']
            secondary = self.devices['secondary']
            parameters = self.get_parameters()
    
            primary_sum = primary.read('CH1')
            secondary_sum = secondary.read('CH1')
    
            for j in range(1, parameters['num']):
                if self.report_progress(j, parameters['num'], start_time):
                    break
    
                # Read scopes
                time.sleep(_SCOPE_AVERAGES / _FREQUENCY)    # Wait until scope averaging is fully refreshed
                data_primary = primary.read('CH1')
                data_secondary = secondary.read('CH1')
    
                primary_sum[:, 1] += data_primary[:, 1]
                secondary_sum[:, 1] += data_secondary[:, 1]
    
            return primary_sum, secondary_sum