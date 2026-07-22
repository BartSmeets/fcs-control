from pathlib import Path

import tomllib

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "configs"

def load_toml(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.toml"
    with open(path, "rb") as f:
        return tomllib.load(f)