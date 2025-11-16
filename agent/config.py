from pydantic_settings import BaseSettings, SettingsConfigDict

class AgentSettings(BaseSettings):
    model_type: str
    model_server: str
    model_name: str
    api_key: str

    model_config = SettingsConfigDict(
        env_file="agent/.env",
        env_file_encoding="utf-8",
        extra='ignore'
    )

settings = AgentSettings()