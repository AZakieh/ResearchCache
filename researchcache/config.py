from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    #Storage
    R2_ENDPOINT_URL: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    REDIS_URL: str = 'redis://localhost:6379/0'
    DATABASE_URL: str

    #Security
    DECISION_HMAC_SECRET: str = Field(..., min_length=64)
    ADMIN_SECRET: str = Field(..., min_length=64)

    ALLOWED_ORIGINS_PATH: Path = 'allowlist.yaml'

    #Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    MAX_OBJECT_SIZE_GB: int = 500

    #Observability
    LOG_LEVEL: str = 'INFO'
    ENVIRONMENT: str = 'development'

    #Feature flags
    ENABLE_API_KEY_AUTH: bool = True
    ENABLE_FEDERATED_IDENTITY: bool = False
    ENABLE_RESTRICTED_DATA: bool = False
    ENABLE_PARALLEL_FETCH: bool = False