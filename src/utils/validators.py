"""
Validation utilities
"""

import logging
from typing import List, Dict, Any
import re

from .geospatial import GeospatialProcessor

logger = logging.getLogger(__name__)
geospatial_processor = GeospatialProcessor()


def validate_coordinates(coordinates: List[List[float]]) -> bool:
    """Validate coordinate format and bounds"""
    return geospatial_processor.validate_coordinates(coordinates)


def validate_area_bounds(coordinates: List[List[float]], max_area_km2: float = 100.0) -> bool:
    """Validate that area is within acceptable bounds"""
    return geospatial_processor.validate_area_bounds(coordinates, max_area_km2)


def validate_email(email: str) -> bool:
    """Validate email format"""
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    except Exception as e:
        logger.error(f"Email validation failed: {str(e)}")
        return False


def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    try:
        if not api_key or len(api_key) < 10:
            return False

        # Basic format validation
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, api_key) is not None
    except Exception as e:
        logger.error(f"API key validation failed: {str(e)}")
        return False


def validate_date_range(date_range: Dict[str, str]) -> bool:
    """Validate date range format"""
    try:
        if not date_range or "start_date" not in date_range or "end_date" not in date_range:
            return False

        start_date = date_range["start_date"]
        end_date = date_range["end_date"]

        # Basic date format validation (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'

        if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
            return False

        # Check if start_date is before end_date
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        return start_dt <= end_dt

    except Exception as e:
        logger.error(f"Date range validation failed: {str(e)}")
        return False


def validate_data_types(data_types: List[str], allowed_types: List[str]) -> bool:
    """Validate data types against allowed list"""
    try:
        if not data_types:
            return True  # Empty list is valid

        return all(data_type in allowed_types for data_type in data_types)

    except Exception as e:
        logger.error(f"Data types validation failed: {str(e)}")
        return False


def validate_analysis_type(analysis_type: str) -> bool:
    """Validate analysis type"""
    allowed_types = ["heat_island", "water_absorption",
                     "air_quality", "comprehensive"]
    return analysis_type in allowed_types


def validate_model_type(model_type: str) -> bool:
    """Validate model type"""
    allowed_types = ["heat_island", "water_absorption",
                     "air_quality", "comprehensive"]
    return model_type in allowed_types


def validate_visualization_type(viz_type: str) -> bool:
    """Validate visualization type"""
    allowed_types = ["heatmap", "before_after",
                     "time_series", "comparison", "3d_model"]
    return viz_type in allowed_types


def validate_confidence_level(confidence_level: float) -> bool:
    """Validate confidence level"""
    return 0.5 <= confidence_level <= 0.99


def validate_time_horizon(time_horizon: int) -> bool:
    """Validate time horizon"""
    return 1 <= time_horizon <= 50


def validate_resolution(resolution: int) -> bool:
    """Validate visualization resolution"""
    return 50 <= resolution <= 1000


def validate_input_data(input_data: Dict[str, Any]) -> bool:
    """Validate input data for ML models"""
    try:
        if not input_data or not isinstance(input_data, dict):
            return False

        # Check for required fields based on data type
        required_fields = ["coordinates", "area_km2"]

        for field in required_fields:
            if field not in input_data:
                return False

        # Validate coordinates
        if not validate_coordinates(input_data["coordinates"]):
            return False

        # Validate area
        if not isinstance(input_data["area_km2"], (int, float)) or input_data["area_km2"] <= 0:
            return False

        return True

    except Exception as e:
        logger.error(f"Input data validation failed: {str(e)}")
        return False
