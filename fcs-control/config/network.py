from pydantic_settings import BaseSettings, SettingsConfigDict

class NetworkSecrets(BaseSettings):
    laser_vision_ip: str
    data_folder: str
    no_network_folder: str

    model_config = SettingsConfigDict(env_file=".env")

def load_network_config():
    return NetworkSecrets()