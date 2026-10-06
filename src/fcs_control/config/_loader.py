from importlib.resources import files

import tomllib


def load_toml(name: str) -> dict:
    path = files("fcs_control.configs").joinpath(f"{name}.toml")

    with open(path, "rb") as f:
        return tomllib.load(f)