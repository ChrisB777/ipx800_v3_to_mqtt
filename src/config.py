"""Configuration module using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration from environment variables."""

    # IPX800 Configuration
    ipx800_host: str = Field(default="192.168.1.100", alias="IPX800_HOST")
    ipx800_port: int = Field(default=80, alias="IPX800_PORT")
    ipx800_username: str = Field(default="admin", alias="IPX800_USERNAME")
    ipx800_password: str = Field(default="", alias="IPX800_PASSWORD")

    # MQTT Configuration
    mqtt_broker_host: str = Field(default="mosquitto", alias="MQTT_BROKER_HOST")
    mqtt_broker_port: int = Field(default=1883, alias="MQTT_BROKER_PORT")
    mqtt_username: str = Field(default="", alias="MQTT_USERNAME")
    mqtt_password: str = Field(default="", alias="MQTT_PASSWORD")
    mqtt_client_id: str = Field(default="ipx800-bridge", alias="MQTT_CLIENT_ID")

    # Bridge Configuration
    http_port: int = Field(default=8080, alias="HTTP_PORT")
    polling_interval: int = Field(default=30, alias="POLLING_INTERVAL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_prefix = ""
        case_sensitive = False


def get_config() -> Config:
    """Get application configuration."""
    return Config()
