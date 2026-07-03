"""
Functions to control the MDO34 Scope

"""
__all__ = ['Scope']

import logging
from struct import unpack

import numpy as np
import pyvisa

from ..config import CHANNEL, HARDWARE
from ..utils.visa import get_resource_manager, get_resources

_logger = logging.getLogger(__name__)

class Scope:
    """
    MDO34 Scope object

    Attributes
    ----------
        visa_resource: obj
            VISA object for scope

        sn: str
            Serial number of the scope found.

        port: str
            Port of the scope found.
    
    Methods
    -------
    read: read data from scope

    runstop: run or stop the scope

    set_micpdiv: set the horizontal scale

    get_micpdiv: get the horizontal scale

    set_samplemode: set scope to sample mode

    set_numavg: set number of shots per read

    """
    def __init__(self, prisec):
        """
        Initialise the Scope object.

        Parameters
        ----------
        prisec: str
            "primary" or "secondary" scope?

        Attributes
        ----------
        visa_resource: obj
            VISA object for scope

        sn: str
            Serial number of the scope found.

        port: str
            Port of the scope found.
        """
        # Connect Scope
        sn = HARDWARE.scope[prisec].serial_number   # configchn.get("PORTS", SN)
        port = HARDWARE.scope[prisec].visa_port
        
        self.visa_resource, self.sn, self.port = self._connect(port,sn)
        _logger.info(f"Using scope at port {self.port} "
                     f"with SN: {self.sn}")
        
        # Initialise settings
        ch_trigger = CHANNEL.scope[prisec].trigger
        self.visa_resource.write(f'TRIGGER:A:EDGE:SOURCE {ch_trigger}')    # Source channel for the A edge trigger
        self.visa_resource.write('HORizontal:DELay:MODe OFF')    # No horizontal delay
        self.visa_resource.write('HORizontal:POSition 10')   # Horizontal position in %
        self.visa_resource.write(':HEAD 0')  # Header off


    def _connect(self, port_name, serial_number):
        '''
        Checks if scope is available: returns the scope object, serial number and port if it is.

        Parameters
        ----------
        port_name: str
            Name of the expected port.
        serial_number: str
            Serial number of the scope.

        Returns
        -------
        visa_resource: obj
            VISA object for the scope.

        sn: str
            Serial number of the scope found.

        port: str
            Port of the scope found.
        
        '''
        resources = get_resources(port_name)
        
        def _identify_resource(resource_name):
            instrument = get_resource_manager().open_resource(resource_name)
            idn = instrument.query("*IDN?")
            return instrument, idn

        if not resources:
            raise NameError("No ports named " + port_name + " found.")

        if len(resources) == 1: # If only one occurence is found, update foundport
            found_port = str(resources[0])
            # Check if serial number matches
            visa_resource, idn = _identify_resource(found_port)

            if serial_number in idn:
                _logger.info(f"The scope with serial number {serial_number} was found")
                sn = serial_number
                port = found_port
            else:
                _logger.warning(f"Scope with serial number {serial_number} was not found. "
                                f"But since only one scope was found, I am using {idn}")
                sn = idn
                port = found_port

            return visa_resource, sn, port

        if len(resources) > 1:
            ## Try if any of the ports matches the serial number
            for resource in resources:  
                try:
                    visa_resource, idn = _identify_resource(found_port)
                    
                    if serial_number in idn:                    
                        _logger.info(f"The scope with serial number {serial_number} was found")
                        sn = serial_number
                        port = found_port
                        return visa_resource, sn, port
                except pyvisa.errors.VisaIOError:
                    _logger.warning(f"I am failing to connect to {resource}, "
                                    f"maybe there is another scope in the list. "
                                    f"I am trying the next device.")
            else:
                raise ValueError(
                    f"""
                    WARNING: Scope with serial number {serial_number} was NOT found.

                    And since there are multiple scopes connected, I cannot just act like I don't care and connect to another scope.
                    """
                )


    def read(self, channel):
        """
        Reads a specific channel of the scope and returns the data.

        Parameters
        ----------
        channel: str
            Channel, e.g., ``"CH1"``

        Returns
        -------
        data : array, shape = (N, 2)
            Array containing the timestamps and voltages

        """
        # Specify the format and location of the transferred waveform data
        self.visa_resource.write(':DATA:SOUrce ' + channel)  # Selects the channel
        self.visa_resource.write(':DATA:WIDTH 1')    # Width in byte per point
        self.visa_resource.write('DATa:Stop 10000000')   # Set the number of data points to the maximum record length
        self.visa_resource.write(':DATA:ENC RPB')    # Encoding format

        # Information needed to interpret the waveform data point
        ymult = float(self.visa_resource.query(':WFMPRE:YMULT?'))    # vertical scale multiplying factor
        yzero = float(self.visa_resource.query(':WFMPRE:YZERO?'))    # vertical offset of the source waveform
        yoff = float(self.visa_resource.query(':WFMPRE:YOFF?'))  # vertical position of the source waveform in digitising levels (25 digitising levels per vertical division)
        t_scale = float(self.visa_resource.query(':WFMPRE:XINCR?'))    # horizontal point spacing in time
        wfm_record = int(self.visa_resource.query('wfmoutpre:nr_pt?'))   # Number of data points
        t_sub = float(self.visa_resource.query('wfmoutpre:xzero?')) # time coordinate of first data point
        pre_trig_record = int(self.visa_resource.query('wfmoutpre:pt_off?')) # Checks if DATA:SOURCE is on or displayed -> generates error if false, 0 if true

        # Transfer waveform data
        bin_wave = self.visa_resource.query_binary_values('curve?', datatype='b', container=np.array)

        # Interpret waveform data
        ## X-axis: time
        total_time = t_scale * wfm_record
        t_start = (-pre_trig_record * t_scale) + t_sub
        t_stop = t_start + total_time
        ## Y-axis: volts
        ADC_wave = bin_wave # [headerlen:-1] header is off
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))
        Volts = (ADC_wave - yoff) * ymult  + yzero
        ## Match dimensions: Exactly one time mark for every datapoint
        scaled_time = np.arange(t_stop-t_scale*len(Volts), t_stop,t_scale)
        
        data = np.transpose([scaled_time,Volts])

        return data


    def runstop(self, runstop):
        """
        Runs or stops the scope depending on the command

        Parameters
        ----------
        runstop: str
            Either 'run' or 'stop'
        
        """
        if runstop.upper()=='RUN':
            self.visa_resource.write(':ACQUIRE:STATE RUN')
        elif runstop.upper()=='STOP':
            self.visa_resource.write(':ACQUIRE:STATE STOP')
        else:
            raise ValueError(f"{runstop} is not a valid command. It's either ``run`` or ``stop``.")
        

    def set_micpdiv(self, micpdiv):
        """
        Set the horizontal time scale in µs/div

        Parameters
        ----------
        micpdiv: str | float | int
            Target value for the horizontal time scale
        
        """
        self.visa_resource.write(f':HOR:SCA {str(micpdiv)}E-6')


    def get_micpdiv(self):
        """
        Read the horizontal time scale in µs/div

        Returns
        -------
        micpdiv : float
            Horizontal time scale in µs/div
        
        """
        micpdiv = self.visa_resource.query(':HOR:SCA?')
        micpdiv = float(micpdiv)*1.e6 # s to us
        return micpdiv


    def set_samplemode(self):
        '''
        Set scope to manual mode
        
        '''
        self.visa_resource.write(':ACQUIRE:MODE SAMPLE')


    def set_numavg(self, average):
        """
        Set the number of shots for the averaging.

        Parameters
        ----------
        average: int
            The number of shots to average for a reading.
        
        """
        if average > 1:
            # Message scope
            self.visa_resource.write(':ACQUIRE:MODE AVERAGE') 
            self.visa_resource.write(f':ACQUIRE:NUMAVG {str(average)}')
        elif average == 1:
            self.set_samplemode()
        else:
            raise ValueError(f"Come on... {average} is not a valid number for averging")
        return