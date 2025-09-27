"""
AlphaEarth API integration for satellite, soil, water, and climate data
"""

import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json

from .base_ingestion import BaseDataIngestion
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlphaEarthDataIngestion(BaseDataIngestion):
    """AlphaEarth API data ingestion class"""

    def __init__(self):
        """Initialize AlphaEarth data ingestion"""
        super().__init__(api_key=settings.ALPHAEARTH_API_KEY)
        self.base_url = "https://api.alphaearth.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def ingest_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from AlphaEarth API

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
                data_types = ["satellite", "soil", "water", "climate"]

            results = {
                "records_ingested": 0,
                "file_paths": [],
                "data_types": data_types,
                "date_range": date_range,
                "coordinates": coordinates,
                "alphaearth_data": {}
            }

            # Ingest each data type from AlphaEarth
            for data_type in data_types:
                try:
                    data_result = await self._ingest_alphaearth_data_type(
                        data_type=data_type,
                        bbox=bbox,
                        date_range=date_range
                    )

                    results["records_ingested"] += data_result["count"]
                    results["file_paths"].extend(data_result["file_paths"])
                    results["alphaearth_data"][data_type] = data_result["data"]

                except Exception as e:
                    logger.error(
                        f"Failed to ingest {data_type} from AlphaEarth: {str(e)}")
                    continue

            logger.info(
                f"AlphaEarth data ingestion completed: {results['records_ingested']} records")
            return results

        except Exception as e:
            logger.error(f"AlphaEarth data ingestion failed: {str(e)}")
            raise

    async def _ingest_alphaearth_data_type(
        self,
        data_type: str,
        bbox: Dict[str, float],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Ingest specific data type from AlphaEarth"""

        # Map data types to AlphaEarth endpoints
        endpoint_mapping = {
            "satellite": "/satellite/imagery",
            "soil": "/soil/analysis",
            "water": "/water/quality",
            "climate": "/climate/weather",
            "vegetation": "/vegetation/ndvi",
            "elevation": "/terrain/elevation",
            "land_cover": "/landcover/classification"
        }

        endpoint = endpoint_mapping.get(data_type, "/satellite/imagery")
        url = f"{self.base_url}{endpoint}"

        # Build request payload
        payload = {
            "bounding_box": {
                "min_lon": bbox["min_lon"],
                "min_lat": bbox["min_lat"],
                "max_lon": bbox["max_lon"],
                "max_lat": bbox["max_lat"]
            },
            "date_range": {
                "start": date_range["start_date"],
                "end": date_range["end_date"]
            },
            "resolution": "high",
            "format": "geotiff"
        }

        # Make request to AlphaEarth API
        async with self.session.post(url, json=payload, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()

                # Save raw data
                filename = f"alphaearth_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                file_path = await self._save_data(data, filename)

                return {
                    "count": 1,
                    "file_paths": [file_path],
                    "data": data
                }
            else:
                error_text = await response.text()
                logger.error(
                    f"AlphaEarth API error {response.status}: {error_text}")
                raise Exception(f"AlphaEarth API error: {response.status}")

    async def get_satellite_imagery(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        resolution: str = "high"
    ) -> Dict[str, Any]:
        """Get satellite imagery from AlphaEarth"""
        try:
            bbox = self._get_bounding_box(coordinates)

            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }

            url = f"{self.base_url}/satellite/imagery"
            payload = {
                "bounding_box": {
                    "min_lon": bbox["min_lon"],
                    "min_lat": bbox["min_lat"],
                    "max_lon": bbox["max_lon"],
                    "max_lat": bbox["max_lat"]
                },
                "date_range": {
                    "start": date_range["start_date"],
                    "end": date_range["end_date"]
                },
                "resolution": resolution,
                "bands": ["red", "green", "blue", "nir", "swir1", "swir2"],
                "format": "geotiff"
            }

            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Satellite imagery request failed: {error_text}")

        except Exception as e:
            logger.error(f"Satellite imagery retrieval failed: {str(e)}")
            raise

    async def get_soil_analysis(
        self,
        coordinates: List[List[float]],
        depth_range: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Get soil analysis data from AlphaEarth"""
        try:
            bbox = self._get_bounding_box(coordinates)

            if not depth_range:
                depth_range = {"min_depth": 0, "max_depth": 100}  # cm

            url = f"{self.base_url}/soil/analysis"
            payload = {
                "bounding_box": {
                    "min_lon": bbox["min_lon"],
                    "min_lat": bbox["min_lat"],
                    "max_lon": bbox["max_lon"],
                    "max_lat": bbox["max_lat"]
                },
                "depth_range": depth_range,
                "parameters": [
                    "moisture_content",
                    "organic_matter",
                    "ph_level",
                    "nutrient_content",
                    "texture",
                    "permeability"
                ],
                "resolution": "medium"
            }

            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Soil analysis request failed: {error_text}")

        except Exception as e:
            logger.error(f"Soil analysis retrieval failed: {str(e)}")
            raise

    async def get_water_quality(
        self,
        coordinates: List[List[float]],
        water_bodies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get water quality data from AlphaEarth"""
        try:
            bbox = self._get_bounding_box(coordinates)

            if not water_bodies:
                water_bodies = ["rivers", "lakes", "groundwater"]

            url = f"{self.base_url}/water/quality"
            payload = {
                "bounding_box": {
                    "min_lon": bbox["min_lon"],
                    "min_lat": bbox["min_lat"],
                    "max_lon": bbox["max_lon"],
                    "max_lat": bbox["max_lat"]
                },
                "water_bodies": water_bodies,
                "parameters": [
                    "temperature",
                    "ph",
                    "dissolved_oxygen",
                    "turbidity",
                    "nutrients",
                    "contaminants",
                    "flow_rate"
                ],
                "temporal_resolution": "daily"
            }

            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Water quality request failed: {error_text}")

        except Exception as e:
            logger.error(f"Water quality retrieval failed: {str(e)}")
            raise

    async def get_climate_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get climate and weather data from AlphaEarth"""
        try:
            bbox = self._get_bounding_box(coordinates)

            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }

            if not parameters:
                parameters = [
                    "temperature",
                    "precipitation",
                    "humidity",
                    "wind_speed",
                    "wind_direction",
                    "pressure",
                    "solar_radiation"
                ]

            url = f"{self.base_url}/climate/weather"
            payload = {
                "bounding_box": {
                    "min_lon": bbox["min_lon"],
                    "min_lat": bbox["min_lat"],
                    "max_lon": bbox["max_lon"],
                    "max_lat": bbox["max_lat"]
                },
                "date_range": {
                    "start": date_range["start_date"],
                    "end": date_range["end_date"]
                },
                "parameters": parameters,
                "temporal_resolution": "hourly",
                "spatial_resolution": "1km"
            }

            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Climate data request failed: {error_text}")

        except Exception as e:
            logger.error(f"Climate data retrieval failed: {str(e)}")
            raise

    async def get_vegetation_analysis(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get vegetation analysis (NDVI, biomass) from AlphaEarth"""
        try:
            bbox = self._get_bounding_box(coordinates)

            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=14)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }

            url = f"{self.base_url}/vegetation/ndvi"
            payload = {
                "bounding_box": {
                    "min_lon": bbox["min_lon"],
                    "min_lat": bbox["min_lat"],
                    "max_lon": bbox["max_lon"],
                    "max_lat": bbox["max_lat"]
                },
                "date_range": {
                    "start": date_range["start_date"],
                    "end": date_range["end_date"]
                },
                "indices": ["ndvi", "ndwi", "evi", "savi"],
                "resolution": "high"
            }

            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Vegetation analysis request failed: {error_text}")

        except Exception as e:
            logger.error(f"Vegetation analysis retrieval failed: {str(e)}")
            raise

    def get_available_data_types(self) -> List[str]:
        """Get list of available AlphaEarth data types"""
        return [
            "satellite",
            "soil",
            "water",
            "climate",
            "vegetation",
            "elevation",
            "land_cover",
            "urban_heat",
            "air_quality",
            "carbon_sequestration"
        ]

    def get_coverage_info(self) -> Dict[str, Any]:
        """Get AlphaEarth data coverage information"""
        return {
            "name": "AlphaEarth",
            "description": "Comprehensive environmental data platform with satellite, soil, water, and climate data",
            "coverage": "global",
            "update_frequency": "real-time",
            "data_types": self.get_available_data_types(),
            "api_documentation": "https://docs.alphaearth.com/api",
            "authentication_required": True,
            "features": [
                "High-resolution satellite imagery",
                "Real-time climate data",
                "Soil composition analysis",
                "Water quality monitoring",
                "Vegetation health indices",
                "Urban heat island detection",
                "Air quality measurements",
                "Carbon sequestration analysis"
            ]
        }
