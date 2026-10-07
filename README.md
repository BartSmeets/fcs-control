# FCS Control

Control software for the FCS setup.

The application provides a graphical user interface (GUI) for automating and running experiments, recording measurement data and logging the settings.

## Table of Contents

- [Features](#features)
- [Modules](#modules)
- [Quick Start](#quick-start)
- [Developer Guide](#developer-guide)
- [Installation](#installation)
- [Configuration](#configuration)

---

## Features

- Device control through VISA and network interfaces:
  - Oscilloscopes
  - Delay generators
  - OPO/OPA system
- Custom experiment automation
- Data acquisition
- Configurable hardware and channel settings
- Modular architecture for adding new devices and experiments

---

## Modules

| Module        | Purpose                                           |
| ------------- | ------------------------------------------------- |
| `config`      | Hardware configuration loading                    |
| `devices`     | Hardware communication and device management      |
| `experiments` | Experiment implementation                         |
| `gui`         | PySide6 GUI                                       |
| `utils`       | Shared utilities such as logging and VISA helpers |

---

## Quick Start

After [installation](#installation):

```bash
fcs-control
```

or, alternatively:

```bash
python -m fcs_control
```

A shortcut to the `.exe` is already made on the desktop of the laboratory computer.

---

## Developer Guide

[Adding an Experiment](#adding-a-new-experiment) | [Adding a Device](#adding-a-new-device)

---

### Adding a New Experiment

#### 1. Create a new experiment module

Do this by making a new Python file in:

```text
src/fcs_control/experiments/
```

During startup, all modules in this directory are automatically imported and scanned for registered experiments.

---

#### 2. Define an `Experiment` class and register it

All communication with the GUI is handled by the base `Experiment` class defined in `_base.py`. Consequently, every new experiment must inherit from `Experiment` and be registered using the `@register_experiment` decorator.
User-configurable inputs are defined through the `Parameter` class and are automatically displayed in the GUI.

The machinery behind this is split over three files in the `experiments` folder, none of which needs to be touched when writing an experiment:

| File           | Purpose                                                                    |
| -------------- | -------------------------------------------------------------------------- |
| `_base.py`     | `Parameter`, `Experiment` (data folder, logbook, devices) and the registry |
| `_progress.py` | Progress tracking, time estimation and abort handling (`self.track()`)     |
| `_runner.py`   | Runs `scan()` on a background thread behind the progress dialog            |

```python
from fcs_control.experiments import Experiment, Parameter, register_experiment

@register_experiment
class Example(Experiment):
    name = "Example"
    description = "This is an example"
    required_devices = ('primaryscope', )

    parameters = (
        Parameter(name='num', label='Number of Cycles', type='int', default=0),
    )
```

##### Required Class Attributes

| Attribute          | Description                                                                   |
| ------------------ | ----------------------------------------------------------------------------- |
| `name`             | Experiment name displayed in the GUI                                          |
| `description`      | Short description of the experiment                                           |
| `required_devices` | Device keys of devices that must be available before the experiment can start |
| `parameters`       | User-configurable parameters shown in the GUI                                 |

---

##### Parameter Options

| Attribute  | Type                                                          | Description                                                                             |
| ---------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `name`     | `str`                                                         | Internal parameter name. Used as the key when retrieving parameter values.              |
| `label`    | `str`                                                         | Human-readable label shown in the GUI.                                                  |
| `type`     | `'int'`, `'float'`, `'short_text'`, `'long_text'`, `'option'` | Determines which input widget is generated.                                             |
| `default`  | `Any`                                                         | Default value shown in the GUI.                                                         |
| `minimum`  | `float`                                                       | Minimum allowed numerical value (if applicable). Default: `0`.                          |
| `maximum`  | `float`                                                       | Maximum allowed numerical value (if applicable). Default: `1e9`.                        |
| `decimals` | `int`                                                         | Number of decimal places for floating-point spin boxes. Default: `1`.                   |
| `options`  | `list[str] \| None`                                           | List of selectable values shown in a combo box. Default: `None`.                        |
| `step`     | `float \| None`                                               | Step size for numerical widgets. Currently, not implemented.                            |
| `unit`     | `str`                                                         | Physical unit associated with the parameter. Currently, not implemented. Default: `''`. |

##### Automatic parameters

Every experiment automatically gets two parameters, which are shown above its own parameters in the GUI:

- `title` ("File Name"): used as the base name of the data files of the run
- `comment`: a free-text box, stored with the other settings in the logbook

Do not define parameters with these names yourself.

---

#### 3. Implement the `scan()` method

The experimental procedure should be implemented in a method named `scan()`:

```python
class Example(Experiment):
    ...

    def scan(self):
        ...
```

This method is executed when the experiment is started from the GUI.

It runs on a **background thread**, so the GUI stays responsive during the scan.
Do not read or change GUI widgets from inside `scan()`: use `self.get_parameters()` (step 5) for the settings, and `self.track()` (step 7) for progress.

---

#### 4. Access devices through the device manager

All required devices are automatically initialized when the experiment starts.

Device instances can be accessed through:

```python
scope = self.devices["primaryscope"]
```

Only devices listed in `required_devices` are available. The keys must match the keys of `DEVICE_CLS` exactly (currently `quantum`, `primaryscope`, `secondaryscope` and `opoopa`); an unknown key raises a `KeyError` when the experiment is started.

The experiment cannot start if a required device is not connected or is in use by another experiment. The devices are reserved exclusively for the duration of the scan, and are released afterwards, also after an abort or a failure.

---

#### 5. Retrieve experiment parameters

The values entered by the user can be obtained as a dictionary using:

```python
parameters = self.get_parameters()
```

The parameter names defined in the `Parameter` objects are used as dictionary keys.

The values are those from the moment the experiment was started. Changing a field in the GUI while the scan is running has no effect on it, and the settings stored in the logbook always match what was actually used. The returned dictionary is a copy, so modifying it does not alter the logged settings.

---

#### 6. Save the data

Every run gets its own data folder and a base file name, both available inside `scan()`:

```python
np.save(self.data_folder / f"{self.filename}.npy", data)
```

- `self.data_folder` is a `Path` to the folder created for this run.
- `self.filename` is the base name of the run, derived from the `title` parameter. Use it as the prefix for every file you save, so that they are grouped with the logbook and settings of the run, which are stored with the same base name. For experiments that produce many files, create a subfolder: `self.data_folder / self.filename`.

Whatever `scan()` returns is stored in `self.result`.

---

#### 7. Report progress and handle aborts

Wrap the main loop of `scan()` in `self.track()`. It updates the progress dialog (bar, elapsed time and estimated remaining time) and handles the Abort button. There is no start time to keep track of and no `break` to write:

```python
def scan(self):
    num = self.get_parameters()['num']

    for i in self.track(range(num), step_time=3.2):
        self.sleep(3.2)     # the work for one step
```

When the user presses Abort, the loop simply ends. No exception is raised, so the code after the loop still runs and can save partial results or clean up.

##### `track()` arguments

| Argument    | Description                                                                                                                                                                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `iterable`  | What to loop over, e.g. `range(num)` or an array of wavelengths.                                                                                                                                                                            |
| `total`     | Number of items. Defaults to `len(iterable)`. Required for generators.                                                                                                                                                                      |
| `step_time` | Expected seconds per item, including everything nested inside it. Optional. Only used on the outermost loop, to give a sensible time estimate from the start. A rough value is enough: the measured pace takes over as the scan progresses. |
| `extra`     | Text shown in the dialog while this loop is active. Either a string, or a function that takes the current item and returns a string (for live read-outs).                                                                                   |

Compute `step_time` from the settings of the experiment where possible, for example the scope averages divided by the trigger frequency.

##### Nested loops

`track()` can be nested. The bar then shows the combined progress of all loops, and the `extra` text of every active loop is shown:

```python
per_wavelength = move_time + num * averages / frequency

for wavelength in self.track(waves,
                             step_time=per_wavelength,
                             extra=lambda wl: f"Wavelength: {wl:.1f} nm"):
    ...
    for _ in self.track(range(num), extra=lambda j: f"Cycle: {j + 1}/{num}"):
        self.sleep(averages / frequency)
        ...
```

##### Waiting and aborting

- Use `self.sleep(seconds)` instead of `time.sleep(seconds)`. It returns immediately when the user aborts, so the user does not have to wait for a long sleep to finish.
- After an aborted inner loop, the rest of the current outer iteration still runs. Check `self.cancel_requested` before using or saving data that would be incomplete:

```python
for wavelength in self.track(waves, step_time=per_wavelength):
    data = self.read_cycles(num)        # contains an inner self.track()
    if self.cancel_requested:           # aborted mid-wavelength: do not save partial data
        break
    np.save(...)
```

Flat experiments that are happy to keep partial data do not need this check.

---

#### 8. Logging

Messages can be written to the GUI log panel using the standard Python logging framework:

```python
import logging
 
logger = logging.getLogger(__name__)
 
logger.info("Starting experiment")
logger.warning("Signal level is low")
```

Log messages automatically appear in the application's log panel.

While an experiment runs, log messages from all modules in `fcs_control.experiments` are also written to the experiment's logbook, `<filename>_log.txt` in the data folder. The logbook starts with the GUI settings, and ends with the final comment entered by the user. Aborts and failures of the scan are logged as well.

---

#### Complete example

An experiment that records the spectrum of a scope over a chosen number of cycles, and puts the steps above together:

```python
import numpy as np

from fcs_control.experiments import Experiment, Parameter, register_experiment

_SCOPE_AVERAGES = 32
_FREQUENCY = 10
_CYCLE_TIME = _SCOPE_AVERAGES / _FREQUENCY   # seconds for the scope to refresh its average


@register_experiment
class Record_RTOF(Experiment):
    name = "Record RTOF"
    description = "Records the RTOF mass spectrum over a chosen amount of cycles."
    required_devices = ('primaryscope',)

    parameters = (
        Parameter('num', 'Number of Cycles', 'int', 0),
    )

    def scan(self):
        num = self.get_parameters()['num']
        scope = self.devices['primaryscope']

        datasum = None
        for _ in self.track(range(num),
                            step_time=_CYCLE_TIME,
                            extra=lambda j: f"Cycle: {j + 1}/{num}"):
            self.sleep(_CYCLE_TIME)      # wait until the scope averaging is fully refreshed
            data = scope.read('CH1')
            if datasum is None:
                datasum = data
            else:
                datasum[:, 1] += data[:, 1]

        if datasum is None:              # aborted before the first cycle finished
            return None

        np.save(self.data_folder / f"{self.filename}.npy", datasum)
        return datasum
```

If the user aborts, the loop ends and the cycles recorded so far are still saved.

---

### Adding a New Device

#### 1. Create a device module

Do this by making a new Python file in:

```text
src/fcs_control/devices/
```

---

#### 2. Define a `class` that implements the device communication

The device manager creates, checks and closes devices without knowing what they are, so the class must provide:

| Member               | Requirement                                                                                                                                                                                                                              |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__(**kwargs)` | Opens the connection, using the `kwargs` from `DEVICE_CLS` (step 3). It must **raise an exception** if the device cannot be reached: the manager then marks the device as offline and logs a warning, and the application keeps running. |
| `is_alive()`         | Returns `True` if the device still responds. The manager uses it to check whether a device is still connected, for example when an experiment is started.                                                                                |
| `disconnect()`       | Closes the connection.                                                                                                                                                                                                                   |

Besides these, add whatever methods the experiments need to talk to the device (for example `read` for a scope).

---

#### 3. Register the device in `devices._device_manager`

This is done by adding it to the `DEVICE_CLS` dictionary. For example:

```python
from ._device import Device

DEVICE_CLS = {
    "device": {
        "class": Device,
        "kwargs": {},   # Keywords for device __init__
        "description": "This is an example",
        "occupied": False,
    },
}
```

##### Required entries

| Key           | Description                                                   |
| ------------- | ------------------------------------------------------------- |
| `class`       | Device implementation class                                   |
| `kwargs`      | Keyword arguments passed to the device constructor            |
| `description` | Human-readable description shown in the GUI                   |
| `occupied`    | Internal flag used by the device manager. Always `False` here |

The key of the entry (`"device"` above) is the name used in `required_devices` and in `self.devices[...]` in experiments.

---

#### 4. Call your device only through `devices.get_device_manager()`

To avoid hundreds of copies of the same device being initiated, the devices are managed globally by the device manager.
Whenever device communication is required, obtain the device instance through the device manager:

```python
from fcs_control.devices import get_device_manager

dm = get_device_manager()
device = dm.get_device('device')
```

This ensures that only a single instance of each device is active throughout the application.

`get_device()` returns the device instance, or `None` if the device is not connected. It raises a `RuntimeError` if the device is reserved by a running experiment.

Inside an experiment, do not call the device manager yourself: list the key in `required_devices` and use `self.devices[...]` (see step 4 of _Adding a New Experiment_).

Other useful members of the device manager:

| Member                               | Purpose                                                                                                              |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| `online`                             | Dictionary of the connected devices, `{key: instance}`                                                               |
| `offline`                            | List of the keys of devices that are not connected                                                                   |
| `is_connected(key)`                  | Whether a specific device is connected                                                                               |
| `refresh_status()`                   | Re-checks whether every device still responds                                                                        |
| `connect_all()` / `disconnect_all()` | Connects or disconnects all devices that are not reserved by a running experiment                                    |
| `reserve(key)`                       | Context manager that reserves a device exclusively. Used by the `Experiment` base class, you normally do not call it |

---

## Installation

### 1. Create environment

```bash
conda create -n fcs-control "python>=3.12"
conda activate fcs-control
```

Python 3.13 is the version the software is developed and tested with.

### 2. Install dependencies

```bash
pip install -e .
```

For offline installation on the laboratory computer:

```bash
pip install -e . --no-build-isolation --no-deps
```

Provided that all required dependencies are already installed in the environment.

Because of installation in editable mode, reinstallation is only required when:

- dependencies change
- package metadata changes
- command line entry points change

---

## Configuration

- Create a `.env` file based on `.env.example`.
- Default device configurations are provided in:

  ```text
  src/fcs_control/configs/
  ```
