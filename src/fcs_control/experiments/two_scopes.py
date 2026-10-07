import numpy as np

from fcs_control.experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10
_STEP_TIME = _SCOPE_AVERAGES / _FREQUENCY

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
        primary_sum, secondary_sum = self._read_cycles()

        if primary_sum or secondary_sum is None:
             return
        
        np.save(self.data_folder / f"{self.filename}_prime.npy", primary_sum)
        np.save(self.data_folder / f"{self.filename}_secon.npy", secondary_sum)

    def _read_cycles(self):
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
            secondary = self.devices['secondaryscope']
            parameters = self.get_parameters()
    
            primary_sum = None
            secondary_sum = None

            for _ in self.track(range(parameters['num']), step_time=_STEP_TIME, extra=lambda j: f"Cycle: {j+1}/{parameters['num']}"):
                # Read scopes
                self.sleep(_SCOPE_AVERAGES / _FREQUENCY)    # Wait until scope averaging is fully refreshed
                data_primary = primary.read('CH1')
                data_secondary = secondary.read('CH1')

                if primary_sum and secondary_sum is None:
                     primary_sum = data_primary
                     secondary_sum = data_secondary
                else:
                    primary_sum[:, 1] += data_primary[:, 1]
                    secondary_sum[:, 1] += data_secondary[:, 1]

            return primary_sum, secondary_sum