"""Configuration management for Cactus Trading Bot."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    app_name: str = "Cactus AI Auto Trader"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Database - InfluxDB 3
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "cactus"
    influxdb_bucket: str = "trading_data"

    # Database - Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_db: int = 0

    # Database - PostgreSQL
    postgres_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/cactus"

    # Exchange API Keys
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None

    # Trading Settings
    max_position_size: float = 0.1  # 10% of account
    max_risk_per_trade: float = 0.02  # 2% of account
    default_leverage: int = 1

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds


# Global settings instance
settings = Settings()
