"""
OpenStreetMap data ingestion module
"""

import logging
from typing import Dict, Any, List, Optional
import json

from .base_ingestion import BaseDataIngestion

logger = logging.getLogger(__name__)


class OSMDataIngestion(BaseDataIngestion):
    """OpenStreetMap data ingestion class"""

    def __init__(self):
        """Initialize OSM data ingestion"""
        super().__init__()  # OSM doesn't require API key
        self.base_url = "https://overpass-api.de/api/interpreter"

    async def ingest_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from OpenStreetMap

        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for data extraction (not used for OSM)
            data_types: Specific data types to extract

        Returns:
            Dictionary with ingestion results
        """
        try:
            bbox = self._get_bounding_box(coordinates)

            # Default data types if not provided
            if not data_types:
                data_types = ["buildings", "roads", "landuse", "waterways"]

            results = {
                "records_ingested": 0,
                "file_paths": [],
                "data_types": data_types,
                "coordinates": coordinates
            }

            # Ingest each data type
            for data_type in data_types:
                try:
                    data_result = await self._ingest_data_type(
                        data_type=data_type,
                        bbox=bbox
                    )

                    results["records_ingested"] += data_result["count"]
                    results["file_paths"].extend(data_result["file_paths"])

                except Exception as e:
                    logger.error(f"Failed to ingest {data_type}: {str(e)}")
                    continue

            logger.info(
                f"OSM data ingestion completed: {results['records_ingested']} records")
            return results

        except Exception as e:
            logger.error(f"OSM data ingestion failed: {str(e)}")
            raise

    async def _ingest_data_type(
        self,
        data_type: str,
        bbox: Dict[str, float]
    ) -> Dict[str, Any]:
        """Ingest specific data type from OSM"""

        # Build Overpass QL query
        query = self._build_overpass_query(data_type, bbox)

        # Make request to Overpass API
        params = {"data": query}
        response = await self._make_request(self.base_url, params=params)

        # Process response
        elements = response.get("elements", [])

        # Save data
        filename = f"osm_{data_type}_{hash(str(bbox))}.json"
        file_path = await self._save_data(response, filename)

        return {
            "count": len(elements),
            "file_paths": [file_path]
        }

    def _build_overpass_query(self, data_type: str, bbox: Dict[str, float]) -> str:
        """Build Overpass QL query for specific data type"""

        # Format bounding box for Overpass
        bbox_str = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"

        # Define queries for different data types
        queries = {
            "buildings": f"""
                [out:json][timeout:25];
                (
                  way["building"]({bbox_str});
                  relation["building"]({bbox_str});
                );
                out geom;
            """,
            "roads": f"""
                [out:json][timeout:25];
                (
                  way["highway"]({bbox_str});
                );
                out geom;
            """,
            "landuse": f"""
                [out:json][timeout:25];
                (
                  way["landuse"]({bbox_str});
                  relation["landuse"]({bbox_str});
                );
                out geom;
            """,
            "waterways": f"""
                [out:json][timeout:25];
                (
                  way["waterway"]({bbox_str});
                );
                out geom;
            """,
            "amenities": f"""
                [out:json][timeout:25];
                (
                  node["amenity"]({bbox_str});
                  way["amenity"]({bbox_str});
                  relation["amenity"]({bbox_str});
                );
                out geom;
            """,
            "natural": f"""
                [out:json][timeout:25];
                (
                  way["natural"]({bbox_str});
                  relation["natural"]({bbox_str});
                );
                out geom;
            """
        }

        return queries.get(data_type, queries["buildings"])

    def get_available_data_types(self) -> List[str]:
        """Get list of available OSM data types"""
        return [
            "buildings",
            "roads",
            "landuse",
            "waterways",
            "amenities",
            "natural",
            "boundaries",
            "public_transport"
        ]

    def get_coverage_info(self) -> Dict[str, Any]:
        """Get OSM data coverage information"""
        return {
            "name": "OpenStreetMap",
            "description": "Open source mapping data",
            "coverage": "global",
            "update_frequency": "continuous",
            "data_types": self.get_available_data_types(),
            "api_documentation": "https://wiki.openstreetmap.org/wiki/Overpass_API",
            "authentication_required": False
        }
