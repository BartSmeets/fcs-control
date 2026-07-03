from pydantic import BaseModel

from ..config._loader import load_toml


class ScopeConfig(BaseModel):
    rtof: str
    trigger: str
    mcp_bended_left: str     # same physical channel as mcp_ltof
    mcp_ltof: str
    current_measure: str     # aka faraday cup; same physical channel as below
    mcp_inj_side: str
    rf_probe: str

class QuantumConfig(BaseModel):
    psv: str
    lamp_right_laser: str   # skimmer side
    lamp_left_laser: str    # PSV side
    extraction: str
    trigger_scope_primary: str
    trigger_scope_secondary: str
    trigger_opo_lamp: str
    trigger_opo_qswitch: str

class QBSConfig(BaseModel):
    ip: int          # Inner pole (right bend) / outer pole (left bend)
    del123: int        # Deflector Exit Lens 1,2,3
    eel2: int          # Entrance Einzel Lens 2
    eel13: int         # Entrance Einzel Lens 1,3
    exel13: int        # Exit Einzel Lens 1,3
    dtbp: int          # Deflector top/bottom plate
    exel2: int         # Exit Einzel Lens 2
    del_entrance: int  # Deflector entrance lens (renamed from "del" — reserved word in Python)
    op: int           # Outer pole (right bend) / outer pole (left bend)

class QMFLConfig(BaseModel):
    velscan: int
    qel: int          # Quad Entrance Lens
    qpf: int
    qexl: int          # Quad Exit Lens
    qexel1: int        # Quad Exit Einzel Lens 1
    qexel2: int
    qexel3: int
    itssel: int        # Ion Trap Source Side Einzel Lens
    itrsel: int       # Ion Trap Ring Side Einzel Lens


class ChannelConfig(BaseModel):
    scope: dict[str, ScopeConfig]
    quantum9520: QuantumConfig
    qbs: QBSConfig
    qmfl: QMFLConfig


def load_channel_config() -> ChannelConfig:
    data = load_toml("channel")
    return ChannelConfig(**data)