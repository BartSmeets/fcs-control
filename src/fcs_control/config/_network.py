from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class NetworkSecrets(BaseSettings):
    laser_vision_ip: str
    data_folder: str
    no_network_folder: str
    msc_address: str

    model_config = SettingsConfigDict(env_file=ROOT / ".env")


def load_network_config():
    return NetworkSecrets()