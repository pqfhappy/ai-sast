from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI-SAST"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./data/sast.db"

    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"

    REDIS_URL: str = "redis://localhost:6379/0"

    CHROMA_PERSIST_DIR: str = "./data/chroma"

    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
