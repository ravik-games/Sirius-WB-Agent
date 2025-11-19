from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODEL_NAME: str
    MODEL_URL: str
    MODEL_API_KEY: str

    TOP_P: float = 0.8
    TOP_K: int = 20
    TEMPERATURE: float = 0.7
    REPETITION_PENALTY: float = 1.0
    PRESENCE_PENALTY: float = 1.5

    model_config = SettingsConfigDict(
        env_file=".env",        
        env_file_encoding="utf-8",
        extra='ignore'
    )

settings = Settings()
