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

    # Database Settings (using Databricks as primary database)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Optional database connection URL (using Databricks as primary)"
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
    DATABRICKS_WAREHOUSE_ID: Optional[str] = Field(
        default=None,
        description="Databricks SQL Warehouse ID (for serverless warehouses)"
    )

    # Data Source API Keys
    ALPHAEARTH_API_KEY: Optional[str] = Field(
        default=None,
        description="AlphaEarth API key for satellite, soil, water, climate, and vegetation data"
    )
    NASA_API_KEY: Optional[str] = Field(
        default=None,
        description="NASA EarthData API key"
    )
    # SENTINEL_API_KEY: Deprecated - Sentinel data now provided via AlphaEarth
    # NOAA_API_KEY: Deprecated - NOAA data now provided via AlphaEarth

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

    # Google Gemini AI API
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for AI chatbot"
    )
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        description="Google API key (alternative name for Gemini API key)"
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

    # Google Earth Engine Settings
    GEE_SERVICE_ACCOUNT: Optional[str] = Field(
        default=None,
        description="Google Earth Engine service account email"
    )
    GEE_KEY_FILE: Optional[str] = Field(
        default=None,
        description="Google Earth Engine service account key file path"
    )
    GEE_PROJECT: Optional[str] = Field(
        default=None,
        description="Google Earth Engine project ID"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()
