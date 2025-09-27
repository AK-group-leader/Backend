"""
Configuration management for the AI-Powered Sustainable Urban Planner
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    HOST: str = Field(default="0.0.0.0", description="API host")
    PORT: int = Field(default=8000, description="API port")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/urban_planner",
        description="Database connection URL"
    )

    # Redis Settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Databricks Settings
    DATABRICKS_HOST: Optional[str] = Field(
        default=None,
        description="Databricks workspace host"
    )
    DATABRICKS_TOKEN: Optional[str] = Field(
        default=None,
        description="Databricks access token"
    )
    DATABRICKS_CLUSTER_ID: Optional[str] = Field(
        default=None,
        description="Databricks cluster ID"
    )

    # Data Source API Keys
    NASA_API_KEY: Optional[str] = Field(
        default=None,
        description="NASA EarthData API key"
    )
    SENTINEL_API_KEY: Optional[str] = Field(
        default=None,
        description="Sentinel Hub API key"
    )
    NOAA_API_KEY: Optional[str] = Field(
        default=None,
        description="NOAA API key"
    )

    # File Storage
    DATA_DIR: str = Field(
        default="data",
        description="Directory for storing data files"
    )
    MODELS_DIR: str = Field(
        default="data/models",
        description="Directory for storing ML models"
    )

    # ML Model Settings
    MODEL_UPDATE_FREQUENCY: int = Field(
        default=30,
        description="Model update frequency in days"
    )
    PREDICTION_CACHE_TTL: int = Field(
        default=3600,
        description="Prediction cache TTL in seconds"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FILE: Optional[str] = Field(
        default=None,
        description="Log file path"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()
