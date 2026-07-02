from .hardware import load_hardware_config, HardwareConfig
from .channel import load_channel_config, ChannelConfig
from .network import load_network_config, NetworkConfig

HARDWARE = load_hardware_config()
CHANNEL = load_channel_config()
NETWORK = load_network_config()
