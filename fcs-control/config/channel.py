from pydantic import BaseModel
from _loader import load_toml

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
    ip: str          # Inner pole (right bend) / outer pole (left bend)
    del123: str        # Deflector Exit Lens 1,2,3
    eel2: str          # Entrance Einzel Lens 2
    eel13: str         # Entrance Einzel Lens 1,3
    exel13: str        # Exit Einzel Lens 1,3
    dtbp: str          # Deflector top/bottom plate
    exel2: str         # Exit Einzel Lens 2
    del_entrance: str  # Deflector entrance lens (renamed from "del" — reserved word in Python)
    op: str           # Outer pole (right bend) / outer pole (left bend)

class QMFLConfig(BaseModel):
    velscan: str
    qel: str           # Quad Entrance Lens
    qpf: str
    qexl: str          # Quad Exit Lens
    qexel1: str        # Quad Exit Einzel Lens 1
    qexel2: str
    qexel3: str
    itssel: str        # Ion Trap Source Side Einzel Lens
    itrsel: str       # Ion Trap Ring Side Einzel Lens


class ChannelConfig(BaseModel):
    scope: dict[str, ScopeConfig]
    quantum9520: QuantumConfig
    qbs: QBSConfig
    qmfl: QMFLConfig


def load_channel_config() -> ChannelConfig:
    data = load_toml("channel")
    return ChannelConfig(**data)