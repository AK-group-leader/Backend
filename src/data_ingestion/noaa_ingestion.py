"""
NOAA data ingestion module
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_ingestion import BaseDataIngestion
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NOAADataIngestion(BaseDataIngestion):
    """NOAA data ingestion class"""

    def __init__(self):
        """Initialize NOAA data ingestion"""
        super().__init__(api_key=settings.NOAA_API_KEY)
        self.base_url = "https://www.ncei.noaa.gov/data"
        self.api_url = "https://www.ncei.noaa.gov/access/services/data/v1"

    async def ingest_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from NOAA

        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for data extraction
            data_types: Specific data types to extract

        Returns:
            Dictionary with ingestion results
        """
        try:
            bbox = self._get_bounding_box(coordinates)

            # Default date range if not provided
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }

            # Default data types if not provided
            if not data_types:
                data_types = ["weather", "climate", "precipitation"]

            results = {
                "records_ingested": 0,
                "file_paths": [],
                "data_types": data_types,
                "date_range": date_range,
                "coordinates": coordinates
            }

            # Ingest each data type
            for data_type in data_types:
                try:
                    data_result = await self._ingest_data_type(
                        data_type=data_type,
                        bbox=bbox,
                        date_range=date_range
                    )

                    results["records_ingested"] += data_result["count"]
                    results["file_paths"].extend(data_result["file_paths"])

                except Exception as e:
                    logger.error(f"Failed to ingest {data_type}: {str(e)}")
                    continue

            logger.info(
                f"NOAA data ingestion completed: {results['records_ingested']} records")
            return results

        except Exception as e:
            logger.error(f"NOAA data ingestion failed: {str(e)}")
            raise

    async def _ingest_data_type(
        self,
        data_type: str,
        bbox: Dict[str, float],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Ingest specific data type from NOAA"""

        # Map data types to NOAA datasets
        dataset_mapping = {
            "weather": "daily-summaries",
            "climate": "normals-daily",
            "precipitation": "precipitation-daily",
            "temperature": "temperature-daily",
            "wind": "wind-daily"
        }

        dataset = dataset_mapping.get(data_type, "daily-summaries")

        # Build request parameters
        params = {
            "dataset": dataset,
            "startDate": date_range["start_date"],
            "endDate": date_range["end_date"],
            "boundingBox": f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}",
            "format": "json",
            "limit": 1000
        }

        # Add API key if available
        headers = {}
        if self.api_key:
            params["token"] = self.api_key

        # Make request
        response = await self._make_request(self.api_url, params=params, headers=headers)

        # Process response
        data_records = response if isinstance(response, list) else [response]

        # Save data
        filename = f"noaa_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = await self._save_data(data_records, filename)

        return {
            "count": len(data_records),
            "file_paths": [file_path]
        }

    def get_available_data_types(self) -> List[str]:
        """Get list of available NOAA data types"""
        return [
            "weather",
            "climate",
            "precipitation",
            "temperature",
            "wind",
            "humidity",
            "pressure",
            "solar_radiation"
        ]

    def get_coverage_info(self) -> Dict[str, Any]:
        """Get NOAA data coverage information"""
        return {
            "name": "NOAA",
            "description": "National Oceanic and Atmospheric Administration weather and climate data",
            "coverage": "global",
            "update_frequency": "hourly",
            "data_types": self.get_available_data_types(),
            "api_documentation": "https://www.ncei.noaa.gov/data/",
            "authentication_required": False
        }
