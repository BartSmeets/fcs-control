import pyvisa

__all__ = ['get_resource_manager']

_rm = pyvisa.ResourceManager()

def get_resource_manager():
    """
    Get the resource manager, duh...

    Returns
    -------
    the resourcemanager...
    """
    return _rm



def identify_resource(resource_name):
    """
    Open a VISA resource and query *IDN?
    """
    instrument = _rm.open_resource(resource_name)
    idn = instrument.query("*IDN?")
    return instrument, idn
