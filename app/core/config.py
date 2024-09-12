from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Subscription Management API"
    ALLOWED_ORIGINS: list = ["*"]
    DATABASE_URL: str = "sqlite:///./subscriptions.db"
    LEMON_SQUEEZY_API_KEY: str
    FIREBASE_PROJECT_ID: str
    STORE_ID: str = "113406"

    class Config:
        env_file = ".env"


settings = Settings()
