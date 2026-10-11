from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Bulk Certificate Generator API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./certificates.db"
    OUTPUT_DIR: str = "./generated_certificates"

    MAX_BATCH_SIZE: int = 100
    MAX_STRING_LENGTH: int = 255

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
