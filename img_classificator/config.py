from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL_NAME: str = "QuantTrio/Qwen3-VL-32B-Instruct-AWQ"
    MODEL_URL: str = "http://195.209.210.28:8000/v1"
    MODEL_API_KEY: str = "sk-no-key-required"

    TOP_P: float = 0.8
    # TOP_K: int = 20
    TEMPERATURE: float = 0.7
    REPETITION_PENALTY: float = 1.0
    PRESENCE_PENALTY: float = 1.5

    # SCREENSHOTS_DIR: str = "screenshots"

    ANALYSIS_PROMPT: str = """
        SYSTEM:
        Тебе передается запрос пользователя в формате JSON, в котором указано, категория товара, и его атрибуты.
        Твоя задача проанализировать насколько то, что изображено на скриншоте соответствует запросу пользователя.
        Если изображение точно соответствует запросу пользователя, верни только OK
        в противном случае - верни ERROR
    """

settings = Settings()
