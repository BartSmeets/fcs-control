from .channel import load_channel_config
from .hardware import load_hardware_config
from .network import load_network_config

HARDWARE = load_hardware_config()
CHANNEL = load_channel_config()
NETWORK = load_network_config()
