import numpy as np

from fcs_control.experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 5
_MOVE_TIME = 5.0    # rough guess for goto_wavelength; the clock corrects it

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
        Parameter('mode', 
                  "Mode", 
                  'option', 
                  'NIR', 
                  options=['NIR', 'IIR', 'MIR']
                  ),
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
        p = self.get_parameters()
        opoopa = self.devices['opoopa']
        opoopa.mode = p['mode']
        num = p['num']

        data_folder = self.data_folder / self.filename
        data_folder.mkdir(exist_ok=True)

        start, stop, step = p['start'], p['stop'], p['step']
        sign = -1 if start > stop else 1
        waves = np.arange(start, stop + 0.1 * step, sign * step)
        if p['unit'] == 'cm-1':
            waves = 1e7 / waves

        def wavelength_info(wl):
            if wl is None:
                return ""
            return (f"Current wavelength: {wl:.1f} nm\n"
                    f"Current wavenumber: {1e7 / wl:.1f} cm⁻¹")

        per_wavelength = _MOVE_TIME + num * _SCOPE_AVERAGES / _FREQUENCY

        for wavelength in self.track(waves, step_time=per_wavelength, extra=wavelength_info):
            opoopa.goto_wavelength(wavelength)
            actual = opoopa.read_wavelength()

            sums = self._read_cycles(num)
            if sums is None:          # aborted mid-wavelength: don't save partial data
                break
            primary_sum, secondary_sum = sums

            np.save(data_folder / f"{self.filename}_{actual}nm_prime.npy", primary_sum)
            np.save(data_folder / f"{self.filename}_{actual}nm_secon.npy", secondary_sum)


    def _read_cycles(self, num: int):
        primary = self.devices['primaryscope']
        secondary = self.devices['secondaryscope']
        primary_sum = secondary_sum = None

        for _ in self.track(range(num), extra=lambda j: f"Cycle: {j + 1}/{num}"):
            self.sleep(_SCOPE_AVERAGES / _FREQUENCY)   # wait for averaging to refresh
            data_p = primary.read('CH1')
            data_s = secondary.read('CH1')
            if primary_sum is None:
                primary_sum, secondary_sum = data_p, data_s
            else:
                primary_sum[:, 1] += data_p[:, 1]
                secondary_sum[:, 1] += data_s[:, 1]

        return None if self.cancel_requested else (primary_sum, secondary_sum)



