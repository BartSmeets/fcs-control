import time

import numpy as np

from ..experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10

@register_experiment
class IR_scan(Experiment):
    name = "IR Scan"
    description = (
        "Record an IR scan over a given IR-range." \
        "The scan records both scopes for comparison with and without IR" \
        "The user should configure the scope triggering accordingly. " \
    )
    required_devices = ('primaryscope', 
                        'secondaryscope', 
                        'opoopa',)

    parameters = (
        Parameter('unit', 
                  "Unit of the IR Values", 
                  'option', 
                  'nm', 
                  options=['nm', 'cm-1']
                  ),
        Parameter('start', 
                  'Starting Value', 
                  'float', 
                  0,
                  decimals = 1),
        Parameter('stop', 
                  'Final Value', 
                  'float', 
                   0,
                   decimals = 1),
        Parameter('step', 
                  'Stepsize', 
                  'float', 
                  0,
                  decimals = 1),
        Parameter('num', 
                  'Number of Cycles', 
                  'int', 
                  0),
    )

    def scan(self):
        start_time = time.time()

        opoopa = self.devices['opoopa']

        parameters = self.get_parameters()
        unit = parameters['unit']
        start = parameters['start']
        stop = parameters['stop']
        step = parameters['step']
        num = parameters['num']

        self.data_folder = self.data_folder / self.filename

        if start > stop:
            waves = np.arange(start, stop + 0.1*step, -step)
        else:
            waves = np.arange(start, stop + 0.1*step, step)

        if unit == 'cm-1':
            waves = 1e7 / waves

        # Scan Wavenumber
        for i, wavelength in enumerate(waves):
            extra = (f"Current wavelength: {wavelength:.1f} nm"
                     f"Current wavenumber: {1e7/wavelength:.1f} cm⁻¹"
                     f"num: 0/{num} ")
            if self.report_progress(i, len(waves), start_time, extra):
                break

            opoopa.goto_wavelength(wavelength)
            wavelength = opoopa.read_wavelength

            primary_sum, secondary_sum = self._read_cycles(waves, i, start_time)

            np.save(self.data_folder / f"{self.filename}_{wavelength}nm_prime.npy", primary_sum)
            np.save(self.data_folder / f"{self.filename}_{wavelength}nm_secon.npy", secondary_sum)

    def _read_cycles(self, waves: np.ndarray, index: int, start_time: float):
        """
        Read the requested number of cycles from the scopes.
        The parameters are only used for updating the progress bar.

        Parameters
        ----------
        waves: ndarray
            Array containing the requested wavelengths.
        index: int
            Index of the current wavelength within `waves`
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
            extra = (f"Current wavelength: {waves[index]:.1f} nm"
                     f"Current wavenumber: {1e7/waves[index]:.1f} cm⁻¹"
                     f"num: {j}/{parameters['num']} ")
            if self.report_progress(j, len(waves), start_time, extra):
                break

            # Read scopes
            time.sleep(_SCOPE_AVERAGES / _FREQUENCY)    # Wait until scope averaging is fully refreshed
            data_primary = primary.read('CH1')
            data_secondary = secondary.read('CH1')

            primary_sum[:, 1] += data_primary[:, 1]
            secondary_sum[:, 1] += data_secondary[:, 1]

        return primary_sum, secondary_sum



