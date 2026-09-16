"""
Functions to control the Quantum 9520 Delay Generator

"""

__all__ = ["Quantum"]

import logging
import string
import time

from ..config import HARDWARE
from ..utils.visa import get_resource_manager, get_resources

_LETTER_LIST = string.ascii_uppercase[:8]
_ONOFF_LIST = ["OFF", "ON"]

_logger = logging.getLogger(__name__)

class Quantum:
    def __init__(self):
        """
        Initialise the Quantum object.
        
        Attributes
        ----------
        visa_resource: obj
            VISA object for the Quantum delay generator

        port: str
            Port of the connection

        settings: dict
            Dictionary containing the settings of the delay generator.
            
            Keys: letters A to H

            Values: dicts containing the settings of each channel:
                
                delay: float
                mode: str
                reference: str
                width: float

        Methods
        -------
        connect: connect device

        disconnect: disconnect device

        is_alive: checks if device still responds

        set_delay: set delay

        set_mode: set operation mode

        set_reference: set channel reference

        set_width: set pulse width

        get_delay: get delay

        get_mode: get operation mode

        get_reference: get channel reference

        get_width: get pulse width

        get_all: collect every setting in a dict

        onoff: turn channel on/off

        t0_normal: set t0 operation mode to normal

        runstop: run/stop the delay generator

        """
        # Connect
        self.visa_resource, self.port = self.connect()
        _logger.info(f"Connected to Quantum 9520 at port {self.port}")
        
        # Read settings
        settings = {}
        for letter in _LETTER_LIST:
            settings[letter] = self.get_all(letter)
        self.settings = settings

    def query(self, query: str, normblocker: bool = True):
        """
        Johan:
        The thing frequently sends a read termination after sending the text "ok" a few times, this will need to filtered out. 
        It also sends the text NORM back sometimes. I checked Baudrate it is correct.. 
        I tried with read but it hinders pyvisa from sending the next command. So like this was the most stable. 
        But NORM can be an actual reply, hence I had to give it as an option.

        Parameters
        ----------
        query: str
            the command to the delay generator
        normblocker: bool (default = True)
            determines if NORM can be accepted as answer
        
        """
        time.sleep(0.1)

        _logger.debug(f"SEND {query}")
        # Initialise and send query
        answer="ok"
        self.visa_resource.write(query)

        # filter 'ok' and/or 'norm'
        if normblocker:
            while (("ok" in answer) or ("NORM" in answer)):
                answer=self.visa_resource.read()
                _logger.debug(f"READ {answer!r}")
        else:
            while ("ok" in answer):
                answer=self.visa_resource.read()
                _logger.debug(f"READ {answer!r}")
        return answer

    def connect(self):
        """
        Connect to Quantum delay generator.

        Parameters
        ----------
        port_name: str
            Port of the Quantum delay generator.

        Returns
        -------
        visa_resource: obj
            VISA object for the delay generator

        found_port: str
            Port where the delay generator was found.
        
        """
        port = HARDWARE.quantum9520.port
        resources = get_resources(port)
        
        if not resources:
            raise NameError(f"No ports named {port} found.")
        elif len(resources) == 1:
            found_port = resources[0]
        else:
            # ----------
            # TO DO: Selection Window
            # ----------
            raise NotImplementedError(
                "I could implement a selection window in case multiple ports are found."
                "But I was not bothered yet.")
        
        # Connect
        visa_resource = get_resource_manager().open_resource(found_port)
        visa_resource.write(':DISP:MOD ON')

        return visa_resource, found_port
    
    def disconnect(self):
        """
        Disconnect the Quantum delay generator
        """
        self.visa_resource.close()
        _logger.info(f"The Quantum delay generator on port {self.port} was disconnected")

    def is_alive(self):
        """
        Check whether the connection to the delay generator is still active.

        Returns
        -------
        bool
            True if the device responds, False if the connection appears lost.

        """
        try:
            _logger.debug(f"ID {self.visa_resource.query("*IDN?")!r}")
            return True
        except Exception as e:  # noqa: BLE001
            _logger.warning(f"Quantum on port {self.port} appears disconnected: {e}")
            return False

    def set_delay(self, channel, dtime):
        """
        Set delay of specified channel

        Parameters
        ----------
        channel: str
            channel letter (A, B, ..., H)

        dtime: float
            time delay in µs

        """
        channel_num = _LETTER_LIST.find(channel) + 1  # channel number, now +1 because at the 9520 A=1
        timeis = f"{dtime * 1e-6:.11f}"  # us to s

        # Set delay
        self.visa_resource.write(f":PULSE{channel_num}:DELAY {timeis}")
        _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")

        _logger.info(f"Delay of CH{channel} on Quantum ({self.port}) is set to {dtime:.2f} µs")

    def set_mode(self, channel, mode):
        '''
        Change delay generator mode

        Parameters
        ----------
        channel: str
            channel
        mode: str
            ``"DCYC"`` for Duty cycle, ``"NORM"`` for normal

        '''
        channel_num = _LETTER_LIST.find(channel) + 1

        self.visa_resource.write(f':PULSE{channel_num}:CMOD {mode}')
        _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")

        if mode.upper()=="DCYC":
            self.visa_resource.write(f':PULSE{channel_num}:PCO 1')
            _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")
            
            self.visa_resource.write(f':PULSE{channel_num}:BCO 1')
            _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")

        _logger.info(f"CH{channel} on Quantum ({self.port}) has been set to mode {mode}")

    def set_reference(self, channel, channel_ref):
        """
        Set reference of specified channel

        Parameters
        ----------
        channel: str
            Channel of which the reference is changed
        
        channel_ref: str
            Reference channel

        """
        channel_num = _LETTER_LIST.find(channel) + 1

        # Set reference (unique message if reference is T=0, hence the if statement)
        if(channel_ref.lower()=="t0" or channel_ref.lower()=="to" or channel_ref.lower()=="t"):
            ref_string = "TO"
        else:
            ref_string = f"CH{channel_ref}"

        self.visa_resource.write(f':PULSE{channel_num}:SYNC {ref_string}')
        _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")

        _logger.info(f"Reference of CH{channel} on Quantum ({self.port}) is set to {ref_string}")

    def set_width(self, channel, dtime):
        """
        Set width of specified channel

        Parameters
        ----------
        channel: str
            channel letter (A, B, ..., H)

        dtime: float
            time delay in µs

        """
        channel_num = _LETTER_LIST.find(channel) + 1  # channel number, now +1 because at the 9520 A=1
        timeis = f"{dtime * 1.e-6:.11f}"  # us to s

        # Set width
        self.visa_resource.write(f":PULSE{channel_num}:WIDTH {timeis}")
        _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")
        
        _logger.info(f"Width of CH{channel} on Quantum ({self.port}) is set to {dtime:.2f} µs")
    
    def get_delay(self, channel):
        """
        Get delay of specified channel

        Parameters
        ----------
        channel: str
            channel letter (A, B, ..., H)

        Returns
        -------
        delay: float
            The requested delay

        """
        channel_num = _LETTER_LIST.find(channel) + 1  # channel number, now +1 because at the 9520 A=1

        delay = float(self.query(f":PULSE{channel_num}:DELAY?"))
        delay *= 1e6
        return delay

    def get_mode(self, channel):
        '''
        Get mode of delay generator

        Parameters
        ----------
        channel: str
            channel

        Returns
        -------
        mode: str
            ``"DCYC"`` for Duty cycle, ``"NORM"`` for normal

        '''
        channel_num = _LETTER_LIST.find(channel) + 1

        mode = self.query(f':PULSE{channel_num}:CMOD?', normblocker=False)
        return mode

    def get_reference(self, channel):
        """
        Set reference of specified channel

        Parameters
        ----------
        channel: str
            Channel of which the reference is changed
        
        Returns
        -------
        channel_ref: str
            Reference channel

        """
        channel_num = _LETTER_LIST.find(channel) + 1

        channel_ref = self.query(f':PULSE{channel_num}:SYNC?')

        # channel_ref looks like CHX -> filter CH
        if channel_ref[0] == 'T':
            return 'T0'
        else:
            return channel_ref[2]

    def get_width(self, channel):
        """
        Set width of specified channel

        Parameters
        ----------
        channel: str
            channel letter (A, B, ..., H)

        width: float
            time delay in µs

        """
        channel_num = _LETTER_LIST.find(channel) + 1  # channel number, now +1 because at the 9520 A=1

        width = float(self.query(f":PULSE{channel_num}:WIDTH?"))
        width *= 1e6
        return width

    def get_all(self, channel):
        """
        Get all settings

        Parameters
        ----------
        channel: str
            Channel letter

        Returns
        -------
        settings: dict
            Dictionary containing the settings:
                
                delay: float
                mode: str
                reference: str
                width: float

        """
        settings = {
            "delay": self.get_delay(channel),
            "mode": self.get_mode(channel),
            "reference": self.get_reference(channel),
            "width": self.get_width(channel)
        }
        return settings

    def onoff(self, channel, onoff):#Turn a channel on or off
        '''
        Turn a channel on/off

        Parameters
        ----------
        channel: str
            channel to turn on/off
        onoff: str
            on/off

        '''
        channel_num = _LETTER_LIST.find(channel) + 1

        # Switch channel
        self.visa_resource.write(f':PULSE{channel_num}:STAT {onoff}')
        _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")

        _logger.info(f"CH{channel} on Quantum ({self.port}) has been switched {_ONOFF_LIST[onoff]}")

    def t0_normal(self):
        '''
        Makes sure the t0 is not in duty cycle
        
        '''
        self.visa_resource.write(':PULSE0:MOD NORM')
        _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")

    def runstop(self, runstop):
        '''
        Run/stop the delay generator

        Parameters
        ----------
        runstop: str
            run/stop

        '''
        if runstop.upper()=="RUN":
            self.visa_resource.write(':PULSE0:STAT ON')
            _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")
        else:
            self.visa_resource.write(':PULSE0:STAT OFF')
            _logger.debug(f"OPC? {self.visa_resource.query("*OPC?")!r}")