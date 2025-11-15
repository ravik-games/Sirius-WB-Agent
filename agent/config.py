from pydantic import BaseSettings

class AgentSettings(BaseSettings):
    model_type: str
    model_server: str
    model_name: str
    api_key: str

    class Config:
        env_file = ".env"

settings = AgentSettings()