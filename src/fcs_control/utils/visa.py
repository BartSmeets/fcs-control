import pyvisa

__all__ = ['get_resource_manager']

_rm = pyvisa.ResourceManager()

def get_resource_manager():
    """
    Get the resource manager, duh...
    
    """
    return _rm


def get_resources(port_name):
    """
    Get resources that match a given port.

    Parameters
    ----------
    port: str
        Port name

    Returns
    -------
    resources: list
        List of resources
    
    """
    resources = [port for port in get_resource_manager().list_resources() if port_name in port]
    return resources