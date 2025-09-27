"""
Base class for data ingestion from external sources
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import aiohttp
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseDataIngestion(ABC):
    """Base class for data ingestion"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize base ingestion class"""
        self.api_key = api_key
        self.session = None
        self.data_dir = Path("data/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def ingest_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from the external source

        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for data extraction
            data_types: Specific data types to extract

        Returns:
            Dictionary with ingestion results
        """
        pass

    @abstractmethod
    def get_available_data_types(self) -> List[str]:
        """Get list of available data types"""
        pass

    @abstractmethod
    def get_coverage_info(self) -> Dict[str, Any]:
        """Get coverage information for the data source"""
        pass

    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        if not self.session:
            raise Exception(
                "Session not initialized. Use async context manager.")

        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Request failed with status {response.status}: {await response.text()}")
                    raise Exception(
                        f"Request failed with status {response.status}")

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise

    def _validate_coordinates(self, coordinates: List[List[float]]) -> bool:
        """Validate coordinate format"""
        if not coordinates or len(coordinates) < 2:
            return False

        for coord in coordinates:
            if not isinstance(coord, list) or len(coord) != 2:
                return False

            lon, lat = coord
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                return False

        return True

    def _get_bounding_box(self, coordinates: List[List[float]]) -> Dict[str, float]:
        """Get bounding box from coordinates"""
        if not self._validate_coordinates(coordinates):
            raise ValueError("Invalid coordinates")

        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]

        return {
            "min_lon": min(lons),
            "max_lon": max(lons),
            "min_lat": min(lats),
            "max_lat": max(lats)
        }

    async def _save_data(self, data: Any, filename: str) -> str:
        """Save data to file"""
        file_path = self.data_dir / filename

        if isinstance(data, dict):
            import json
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            with open(file_path, 'wb') as f:
                f.write(data)

        logger.info(f"Data saved to {file_path}")
        return str(file_path)
