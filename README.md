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

#### 2. Define a `Experiment` class and register it

All communication with the GUI is handled by the base `Experiment` class defined in `_base.py`. Consequently, every new experiment must inherit from `Experiment` and be registered using the `@register_experiment` decorator.
User-configurable inputs are defined through the `Parameter` class and are automatically displayed in the GUI.

```python
from fcs_control.experiments import Experiment, Parameter, register_experiment

@register_experiment
class Example(Experiment):
    name = "Example"
    description = "This is an example"
    required_devices = ('primaryscope', )

    parameters = (
        Parameter(name='num', label='Number of Cycles', type='int', default=0)
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

| Attribute  | Type                                   | Description                                                                             |
| ---------- | -------------------------------------- | --------------------------------------------------------------------------------------- |
| `name`     | `str`                                  | Internal parameter name. Used as the key when retrieving parameter values.              |
| `label`    | `str`                                  | Human-readable label shown in the GUI.                                                  |
| `type`     | `'int'`, `'short_text'`, `'long_text'` | Determines which input widget is generated.                                             |
| `default`  | `Any`                                  | Default value shown in the GUI.                                                         |
| `minimum`  | `float`                                | Minimum allowed numerical value (if applicable). Default: `0`.                          |
| `maximum`  | `float`                                | Maximum allowed numerical value (if applicable). Default: `0`.                          |
| `decimals` | `int`                                  | Number of decimal places for floating-point spin boxes. Default: `1`.                   |
| `options`  | `list \| None`                         | List of selectable values shown in a combo box. Default: `None`.                        |
| `step`     | `float \| None`                        | Step size for numerical widgets. Currently, not implemented.                            |
| `unit`     | `str`                                  | Physical unit associated with the parameter. Currently, not implemented. Default: `''`. |

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

---

#### 4. Access devices through the device manager

All required devices are automatically initialized when the experiment starts.

Device instances can be accessed through:

```python
scope = self.devices["primaryscope"]
```

---

#### 5. Retrieve experiment parameters

The values entered by the user can be obtained as a dictionary using:

```python
parameters = self.get_parameters()
```

The parameter names defined in the `Parameter` objects are used as dictionary keys.

---

#### 6. Report experiment progress

The base class provides a helper method for updating the progress dialog:

```python
if self.report_progress(progress, total, start_time):
break
```

where:

- `progress` is the current iteration number
- `total` is the expected total number of iterations
- `start_time` is the timestamp recorded at the start of the experiment

The method returns `True` if the user has requested to abort the experiment. In that case, the scan loop should be terminated:

```python
for i in range(total):
 
if self.report_progress(i, total, start_time):
break
 
...
```

---

#### 7. Logging

Messages can be written to the GUI log panel using the standard Python logging framework:

```python
import logging
 
logger = logging.getLogger(__name__)
 
logger.info("Starting experiment")
logger.warning("Signal level is low")
```

Log messages automatically appear in the application's log panel.

---

### Adding a New Device

#### 1. Create a device module

Do this by making a new Python file in:

```text
src/fcs_control/devices/
```

---

#### 2. Define a `class` that implements the device communication

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

| Key           | Description                                        |
| ------------- | -------------------------------------------------- |
| `class`       | Device implementation class                        |
| `kwargs`      | Keyword arguments passed to the device constructor |
| `description` | Human-readable description shown in the GUI        |
| `occupied`    | Internal flag used by the device manager           |

---

#### 4. Call your device only through `devices.get_device_manager()`

To avoid hundreds copies of the same device being initiated, the devices are managed globally by the device manager.
Whenever device communication is required, obtain the device instance through the device manager:

```python
from fcs_control.devices import get_device_manager

dm = get_device_manager()
device = dm['device']
```

This ensures that only a single instance of each device is active throughout the application.

---

## Installation

### 1. Create environment

```bash
conda create -n fcs-control
conda activate fcs-control
```

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
