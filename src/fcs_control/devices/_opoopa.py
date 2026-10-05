"""
Functions to control the OPO/OPA

"""

import logging
import subprocess
import time
from typing import Literal

from ..config import HARDWARE, NETWORK

_logger = logging.getLogger(__name__)

_YAG = 1064.46   # YAG Wavelength
_WAIT = 2.0  # Waiting time in seconds (s)
_TIMEOUT = 300.0 # seconds (s) -> 5 min


class Opoopa:
    """
    OPO/OPA System

    Attributes
    ----------
    msc_address: str, from NETWORK
        Location of `MotorSendCmd.exe`
    ip: str, from NETWORK
        IP address of the OPO/OPA PC
    port: str, from NETWORK
        Connection port of the OPO/OPA to the PC
    mode: ['NIR', 'IIR', 'MIR']
        Operating mode 
        -> the orientation of the final filter

    Methods
    -------
    goto_wavelength
        Move the OPO/OPA to a given wavelength
    goto_wavenumber
        Move the OPO/OPA to a given wavenumber
    read_wavelength
        Read the wavelength from the OPO/OPA PC
    read_wavenumber
        Read the wavenumber from the OPO/OPA PC
    is_alive
        Checks if the OPO/OPA is (still) connected

    """
    _msc_address = NETWORK.msc_address
    _ip = NETWORK.laser_vision_ip
    _port = str(HARDWARE.laser_vision.port)

    mode: Literal['NIR', 'IIR', 'MIR'] = 'NIR'

    def __init__(self):
        """
        Sends a command to read the wavelength
        to test if the OPO/OPA is connected

        """
        self._read_nir()

    def goto_wavelength(self, wavelength: float, timeout: float = _TIMEOUT) -> None:
        """
        Move the OPO/OPA to a given wavelength

        Parameters
        ----------
        wavelength: float
            target wavelength in nanometers (nm)
        timeout: float, optional
            Timeout time for waiting for the motor to finish
        
        """
        self._sendnir(self._wavelength2nir(wavelength))

        _logger.info(f"OPO/OPA: started moving to {wavelength} nm ({1e7/wavelength} cm⁻¹)")
        start = time.monotonic()

        while True:
            if not self._wait():
                _logger.info(f"OPO/OPA: finished moving to {wavelength} nm ({1e7/wavelength} cm⁻¹)")
                return
            
            elif time.monotonic() - start > timeout:
                raise TimeoutError(
                    f"OPO/OPA did not reach {wavelength} nm ({1e7/wavelength} cm⁻¹) within {timeout} s"
                )

            else:
                _logger.debug("Motor is still moving...")
                time.sleep(_WAIT)

    def goto_wavenumber(self, wavenumber: float, timeout: float = _TIMEOUT) -> None:
        """
        Move the OPO/OPA to a given wavenumber

        Parameters
        ----------
        wavenumber: float
            target wavenumber in cm⁻¹
        timeout: float, optional
            Timeout time for waiting for the motor to finish
        
        """
        self.goto_wavelength(1e7 / wavenumber, timeout)

    def read_wavelength(self) -> float:
        """
        Read the wavelength from the OPO/OPA PC

        Returns
        -------
        wavelength: float
            wavelength in nanometer (nm)
        """
        return self._nir2wavelength(self._read_nir())

    def read_wavenumber(self) -> float:
        """
        Read the wavenumber from the OPO/OPA PC

        Returns
        -------
        wavenumber: float
            wavenumber in cm⁻¹

        """
        return 1e7 / self.read_wavelength()

    def is_alive(self) -> bool:
        try:
            self._read_nir()
            return True
        except (FileNotFoundError, PermissionError, OSError) as e:
            _logger.warning(f"Failed to launch MotorSendCmd.exe: {e}")
            return False
        except RuntimeError as e:
            _logger.warning(f"Communication failed: {e}")
            return False
    
    def _sendnir(self, nir:float) -> None:
        """
        Send the NIR communication to the OPO/OPA PC

        Parameters
        ----------
        nir: float
            nir wavelength in nanometer (nm)
        
        """
        code = 5

        while code == 5:
            result = subprocess.run([
                self._msc_address,
                "-a",
                self._ip,
                "-p",
                self._port,
                "-c",
                f"GOTO {nir}",
                "--check"], 
                capture_output = True, 
                text = True,
                check = False
                )
            code = int(result.stdout)
            _logger.debug(f"SEND CODE: {code}")

            if code == 0:
                return
            if code == 3:
                raise ValueError(f"NIR Value {nir} is out of range")

    def _read_nir(self) -> float:
        """
        Read the nir wavelength from the OPO/OPA PC

        Returns
        -------
        nir: float
            Current nir wavelength

        """
        result = subprocess.run([
            self._msc_address,
            "-a",
            self._ip,
            "-p",
            self._port,
            "-c",
            "TELLWL"], 
            capture_output = True, 
            text = True,
            check = False,
            )
        
        try:
            return float(result.stdout)
        except ValueError as e:
            raise RuntimeError(
                f"Unexpected response from OPO/OPA: {result.stdout!r}"
                ) from e

    def _wavelength2nir(self, wavelength: float) -> float:
        """
        Convert a wavelength into the corrsponding nir wavelength,
        given the mode of the OPO/OPA.

        Parameters
        ----------
        wavelength: int | float
            wavelength in nanometer (nm)
        
        Returns
        -------
        nir: float
            NIR wavelength

        """
        if self.mode == 'NIR':
            return float(wavelength)
        elif self.mode == 'IIR':
            return 1 / (2 / _YAG - 1 / wavelength)
        elif self.mode == 'MIR':
            return 1 / (1 / _YAG + 1 / wavelength)

    def _nir2wavelength(self, nir: float) -> float:
            """
            Convert a nir wavelength into the corrsponding wavelength of the mode of the OPO/OPA.
    
            Parameters
            ----------
            nir: float
                nir wavelength in nanometer (nm)
            
            Returns
            -------
            wavelength: float
                wavelength in (nm)
    
            """
            if self.mode == 'NIR':
                return float(nir)
            elif self.mode == 'IIR':
                return 1 / (2 / _YAG - 1 / nir)
            elif self.mode == 'MIR':
                return 1 / (1 / nir - 1 / _YAG)

    def _wait(self, reducing: bool=True) -> bool:
        """
        Checks if the motors have stopped moving
        and answers the question whether we should wait.

        Parameters
        ----------
        reducing: bool, default = True
            Should we wait fot the motors to finish "reducing errors"?

        Returns
        -------
        wait: bool
            Boolean stating if the motor is still moving
            or reducing errors.
            Answers the question if we should wait.
        
        """
        result = subprocess.run([
            self._msc_address,
            "-a",
            self._ip,
            "-p",
            self._port,
            "-c",
            "TELLSTAT",], 
            capture_output = True, 
            text = True,
            check = False
            )
        
        hexval = int(str(result.stdout), 0)
        binval = str(format(hexval, '0>13b'))
        _logger.debug(f"WAIT HEX: {hexval}")

        return (hexval > 0 and reducing) or (binval[-1] != binval[-2] and not reducing)