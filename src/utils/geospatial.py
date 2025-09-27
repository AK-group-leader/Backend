"""
Geospatial processing utilities
"""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point
from shapely.ops import transform
import pyproj
from functools import partial

logger = logging.getLogger(__name__)


class GeospatialProcessor:
    """Geospatial processing utilities"""

    def __init__(self):
        """Initialize geospatial processor"""
        self.wgs84 = pyproj.CRS('EPSG:4326')
        self.utm = None  # Will be determined based on coordinates

    def validate_coordinates(self, coordinates: List[List[float]]) -> bool:
        """Validate coordinate format and bounds"""
        try:
            if not coordinates or len(coordinates) < 3:
                return False

            for coord in coordinates:
                if not isinstance(coord, list) or len(coord) != 2:
                    return False

                lon, lat = coord
                if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                    return False

            return True

        except Exception as e:
            logger.error(f"Coordinate validation failed: {str(e)}")
            return False

    def validate_area_bounds(self, coordinates: List[List[float]], max_area_km2: float = 100.0) -> bool:
        """Validate that area is within acceptable bounds"""
        try:
            area_km2 = self.calculate_area_km2(coordinates)
            return area_km2 <= max_area_km2

        except Exception as e:
            logger.error(f"Area bounds validation failed: {str(e)}")
            return False

    def calculate_area_km2(self, coordinates: List[List[float]]) -> float:
        """Calculate area in square kilometers"""
        try:
            # Create polygon
            polygon = Polygon(coordinates)

            # Determine appropriate UTM zone
            centroid = polygon.centroid
            utm_zone = self._get_utm_zone(centroid.x, centroid.y)
            utm_crs = pyproj.CRS(f'EPSG:{utm_zone}')

            # Transform to UTM for accurate area calculation
            transformer = pyproj.Transformer.from_crs(
                self.wgs84, utm_crs, always_xy=True)
            utm_polygon = transform(transformer.transform, polygon)

            # Calculate area in square meters, then convert to km²
            area_m2 = utm_polygon.area
            area_km2 = area_m2 / 1_000_000

            return area_km2

        except Exception as e:
            logger.error(f"Area calculation failed: {str(e)}")
            return 0.0

    def get_bounding_box(self, coordinates: List[List[float]]) -> Dict[str, float]:
        """Get bounding box from coordinates"""
        try:
            if not self.validate_coordinates(coordinates):
                raise ValueError("Invalid coordinates")

            lons = [coord[0] for coord in coordinates]
            lats = [coord[1] for coord in coordinates]

            return {
                "min_lon": min(lons),
                "max_lon": max(lons),
                "min_lat": min(lats),
                "max_lat": max(lats)
            }

        except Exception as e:
            logger.error(f"Bounding box calculation failed: {str(e)}")
            raise

    def create_polygon(self, coordinates: List[List[float]]) -> Polygon:
        """Create Shapely polygon from coordinates"""
        try:
            if not self.validate_coordinates(coordinates):
                raise ValueError("Invalid coordinates")

            return Polygon(coordinates)

        except Exception as e:
            logger.error(f"Polygon creation failed: {str(e)}")
            raise

    def point_in_polygon(self, point: Tuple[float, float], polygon_coords: List[List[float]]) -> bool:
        """Check if point is inside polygon"""
        try:
            polygon = self.create_polygon(polygon_coords)
            point_geom = Point(point[0], point[1])
            return polygon.contains(point_geom)

        except Exception as e:
            logger.error(f"Point in polygon check failed: {str(e)}")
            return False

    def buffer_polygon(self, coordinates: List[List[float]], buffer_km: float) -> List[List[float]]:
        """Buffer polygon by specified distance in kilometers"""
        try:
            polygon = self.create_polygon(coordinates)

            # Convert buffer distance to degrees (approximate)
            buffer_degrees = buffer_km / 111.32  # Rough conversion

            # Apply buffer
            buffered_polygon = polygon.buffer(buffer_degrees)

            # Extract coordinates
            if hasattr(buffered_polygon, 'exterior'):
                coords = list(buffered_polygon.exterior.coords)
                return [[coord[0], coord[1]] for coord in coords]
            else:
                # Handle case where buffer creates multiple polygons
                coords = list(buffered_polygon.geoms[0].exterior.coords)
                return [[coord[0], coord[1]] for coord in coords]

        except Exception as e:
            logger.error(f"Polygon buffering failed: {str(e)}")
            return coordinates

    def simplify_polygon(self, coordinates: List[List[float]], tolerance: float = 0.001) -> List[List[float]]:
        """Simplify polygon by reducing number of points"""
        try:
            polygon = self.create_polygon(coordinates)
            simplified_polygon = polygon.simplify(
                tolerance, preserve_topology=True)

            coords = list(simplified_polygon.exterior.coords)
            return [[coord[0], coord[1]] for coord in coords]

        except Exception as e:
            logger.error(f"Polygon simplification failed: {str(e)}")
            return coordinates

    def calculate_centroid(self, coordinates: List[List[float]]) -> Tuple[float, float]:
        """Calculate centroid of polygon"""
        try:
            polygon = self.create_polygon(coordinates)
            centroid = polygon.centroid
            return (centroid.x, centroid.y)

        except Exception as e:
            logger.error(f"Centroid calculation failed: {str(e)}")
            return (0.0, 0.0)

    def calculate_distance_km(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in kilometers"""
        try:
            # Use Haversine formula for great circle distance
            lat1, lon1 = point1
            lat2, lon2 = point2

            # Convert to radians
            lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * \
                np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arcsin(np.sqrt(a))

            # Earth's radius in kilometers
            r = 6371

            return c * r

        except Exception as e:
            logger.error(f"Distance calculation failed: {str(e)}")
            return 0.0

    def _get_utm_zone(self, lon: float, lat: float) -> int:
        """Get UTM zone number for given longitude and latitude"""
        try:
            # UTM zone calculation
            utm_zone = int((lon + 180) / 6) + 1

            # Handle special cases
            if lat >= 56.0 and lat < 64.0 and lon >= 3.0 and lon < 12.0:
                utm_zone = 32
            elif lat >= 72.0 and lat < 84.0:
                if lon >= 0.0 and lon < 9.0:
                    utm_zone = 31
                elif lon >= 9.0 and lon < 21.0:
                    utm_zone = 33
                elif lon >= 21.0 and lon < 33.0:
                    utm_zone = 35
                elif lon >= 33.0 and lon < 42.0:
                    utm_zone = 37

            # Determine hemisphere
            if lat >= 0:
                utm_zone += 32600  # Northern hemisphere
            else:
                utm_zone += 32700  # Southern hemisphere

            return utm_zone

        except Exception as e:
            logger.error(f"UTM zone calculation failed: {str(e)}")
            return 32601  # Default to UTM Zone 1N
