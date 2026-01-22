from pydantic_settings import BaseSettings, SettingsConfigDict

class GlobalConfig(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int   
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    ALLOWED_EMAIL_DOMAINS: list[str]
    REDIS_URL: str
    DOMAIN: str 
    # B2_KEY_ID: str
    # B2_APPLICATION_KEY: str
    # B2_BUCKET_NAME: str = "Quicklet"
    # B2_BUCKET_ID: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

class ProductionConfig(GlobalConfig):
    ...

class DevelopmentConfig(GlobalConfig):
    CORS_ORIGIN: str


Config = GlobalConfig()