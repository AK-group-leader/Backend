"""
NASA EarthData ingestion module
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_ingestion import BaseDataIngestion
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NASADataIngestion(BaseDataIngestion):
    """NASA EarthData ingestion class"""

    def __init__(self):
        """Initialize NASA data ingestion"""
        super().__init__(api_key=settings.NASA_API_KEY)
        self.base_url = "https://cmr.earthdata.nasa.gov/search"
        self.granule_url = "https://cmr.earthdata.nasa.gov/search/granules"

    async def ingest_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from NASA EarthData

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
                data_types = ["landsat", "modis", "sentinel-2"]

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
                f"NASA data ingestion completed: {results['records_ingested']} records")
            return results

        except Exception as e:
            logger.error(f"NASA data ingestion failed: {str(e)}")
            raise

    async def _ingest_data_type(
        self,
        data_type: str,
        bbox: Dict[str, float],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Ingest specific data type from NASA"""

        # Map data types to NASA collection IDs
        collection_mapping = {
            "landsat": "C1150038576-NSIDC_ECS",  # Landsat 8
            "modis": "C1150038576-NSIDC_ECS",     # MODIS
            "sentinel-2": "C1150038576-NSIDC_ECS",  # Sentinel-2
            "temperature": "C1150038576-NSIDC_ECS",
            "precipitation": "C1150038576-NSIDC_ECS"
        }

        collection_id = collection_mapping.get(
            data_type, "C1150038576-NSIDC_ECS")

        # Build search parameters
        params = {
            "collection_concept_id": collection_id,
            "bounding_box": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}",
            "temporal": f"{date_range['start_date']}T00:00:00Z,{date_range['end_date']}T23:59:59Z",
            "page_size": 100,
            "format": "json"
        }

        # Add API key if available
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Search for granules
        search_url = f"{self.granule_url}.json"
        search_response = await self._make_request(search_url, params=params, headers=headers)

        granules = search_response.get("feed", {}).get("entry", [])

        file_paths = []
        for granule in granules:
            try:
                # Get granule details
                granule_id = granule.get("id", "")
                granule_url = f"{self.granule_url}/{granule_id}.json"

                granule_response = await self._make_request(granule_url, headers=headers)
                granule_data = granule_response.get(
                    "feed", {}).get("entry", {})

                # Save granule metadata
                filename = f"nasa_{data_type}_{granule_id}.json"
                file_path = await self._save_data(granule_data, filename)
                file_paths.append(file_path)

            except Exception as e:
                logger.error(
                    f"Failed to process granule {granule.get('id', 'unknown')}: {str(e)}")
                continue

        return {
            "count": len(granules),
            "file_paths": file_paths
        }

    def get_available_data_types(self) -> List[str]:
        """Get list of available NASA data types"""
        return [
            "landsat",
            "modis",
            "sentinel-2",
            "temperature",
            "precipitation",
            "vegetation",
            "soil_moisture",
            "snow_cover"
        ]

    def get_coverage_info(self) -> Dict[str, Any]:
        """Get NASA data coverage information"""
        return {
            "name": "NASA EarthData",
            "description": "NASA's Earth observation data archive",
            "coverage": "global",
            "update_frequency": "daily",
            "data_types": self.get_available_data_types(),
            "api_documentation": "https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html",
            "authentication_required": True
        }
