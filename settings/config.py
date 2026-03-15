from pydantic_settings import BaseSettings, SettingsConfigDict

class Configs(BaseSettings):
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
    REDIS_URL: str
    DOMAIN: str 
    UPLOAD_PATH: str
    BASE_DIR: str  
    CACHE_EXPIRATION_TIME: int


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

# class ProductionConfig(GlobalConfig):
#     ...

# class DevelopmentConfig(GlobalConfig):
#     CORS_ORIGIN: str


GlobalConfig = Configs() # type: ignore

def get_config() -> Configs:
    return GlobalConfig