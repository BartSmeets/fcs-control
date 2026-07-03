from pydantic import BaseModel

from ..config._loader import load_toml


class ScopeChannel(BaseModel):
    visa_port: str
    serial_number: str

class Dg535Channel(BaseModel):
    gpib_address: int

class FugChannel(BaseModel):
    port: str


# --- Models for single-instance sections ---

class SerialInstrument(BaseModel):
    port: str

class LaserVision(BaseModel):
    port: int


# --- Top-level config ---

class HardwareConfig(BaseModel):
    scope: dict[str, ScopeChannel]
    quantum9520: SerialInstrument
    dg535: dict[str, Dg535Channel]
    qbs: SerialInstrument
    qmfl: SerialInstrument
    esi_ps: SerialInstrument
    fug: dict[str, FugChannel]
    laser_vision: LaserVision


def load_hardware_config() -> HardwareConfig:
    data = load_toml("hardware")
    return HardwareConfig(**data)