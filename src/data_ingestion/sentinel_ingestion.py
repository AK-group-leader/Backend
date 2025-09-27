"""
Sentinel Hub ingestion module
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_ingestion import BaseDataIngestion
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SentinelDataIngestion(BaseDataIngestion):
    """Sentinel Hub ingestion class"""

    def __init__(self):
        """Initialize Sentinel Hub data ingestion"""
        super().__init__(api_key=settings.SENTINEL_API_KEY)
        self.base_url = "https://services.sentinel-hub.com/api/v1"
        self.process_url = f"{self.base_url}/process"

    async def ingest_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from Sentinel Hub

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
                data_types = ["sentinel-2", "sentinel-1"]

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
                f"Sentinel data ingestion completed: {results['records_ingested']} records")
            return results

        except Exception as e:
            logger.error(f"Sentinel data ingestion failed: {str(e)}")
            raise

    async def _ingest_data_type(
        self,
        data_type: str,
        bbox: Dict[str, float],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Ingest specific data type from Sentinel Hub"""

        # Map data types to Sentinel collections
        collection_mapping = {
            "sentinel-1": "sentinel-1-grd",
            "sentinel-2": "sentinel-2-l2a",
            "sentinel-3": "sentinel-3-olci",
            "dem": "dem"
        }

        collection = collection_mapping.get(data_type, "sentinel-2-l2a")

        # Build process request
        process_request = {
            "input": {
                "bounds": {
                    "bbox": [bbox['min_lon'], bbox['min_lat'], bbox['max_lon'], bbox['max_lat']],
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": collection,
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{date_range['start_date']}T00:00:00Z",
                                "to": f"{date_range['end_date']}T23:59:59Z"
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": self._get_evalscript(data_type)
        }

        # Add API key to headers
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Make process request
        response = await self._make_request(
            self.process_url,
            method="POST",
            json=process_request,
            headers=headers
        )

        # Save response data
        filename = f"sentinel_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = await self._save_data(response, filename)

        return {
            "count": 1,
            "file_paths": [file_path]
        }

    def _get_evalscript(self, data_type: str) -> str:
        """Get evalscript for specific data type"""
        evalscripts = {
            "sentinel-1": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["VV", "VH"],
                        output: { bands: 3 }
                    };
                }
                function evaluatePixel(sample) {
                    return [sample.VV, sample.VH, sample.VV / sample.VH];
                }
            """,
            "sentinel-2": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B02", "B03", "B04", "B08"],
                        output: { bands: 4 }
                    };
                }
                function evaluatePixel(sample) {
                    return [sample.B04, sample.B03, sample.B02, sample.B08];
                }
            """,
            "dem": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["DEM"],
                        output: { bands: 1 }
                    };
                }
                function evaluatePixel(sample) {
                    return [sample.DEM];
                }
            """
        }

        return evalscripts.get(data_type, evalscripts["sentinel-2"])

    def get_available_data_types(self) -> List[str]:
        """Get list of available Sentinel data types"""
        return [
            "sentinel-1",
            "sentinel-2",
            "sentinel-3",
            "dem",
            "land_cover",
            "ndvi",
            "ndwi"
        ]

    def get_coverage_info(self) -> Dict[str, Any]:
        """Get Sentinel Hub coverage information"""
        return {
            "name": "Sentinel Hub",
            "description": "European Space Agency satellite data",
            "coverage": "global",
            "update_frequency": "daily",
            "data_types": self.get_available_data_types(),
            "api_documentation": "https://docs.sentinel-hub.com/api/",
            "authentication_required": True
        }
