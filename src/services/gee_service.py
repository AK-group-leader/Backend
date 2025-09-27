"""
Google Earth Engine Service for Urban Heat Island Mapping, 
Green Space Optimization, and Sustainable Building Zones Analysis
"""

import logging
import ee
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GoogleEarthEngineService:
    """Google Earth Engine service for environmental analysis"""
    
    def __init__(self):
        """Initialize Google Earth Engine service"""
        self.initialized = False
        self.project_id = settings.GEE_PROJECT
        
        try:
            self._initialize_gee()
        except Exception as e:
            logger.error(f"Failed to initialize Google Earth Engine: {str(e)}")
            raise
    
    def _initialize_gee(self):
        """Initialize Google Earth Engine with authentication"""
        try:
            if settings.GEE_SERVICE_ACCOUNT and settings.GEE_KEY_FILE:
                # Service account authentication
                key_file_path = os.path.join(os.getcwd(), settings.GEE_KEY_FILE)
                if os.path.exists(key_file_path):
                    credentials = ee.ServiceAccountCredentials(
                        settings.GEE_SERVICE_ACCOUNT,
                        key_file_path
                    )
                    ee.Initialize(credentials, project=self.project_id)
                else:
                    raise FileNotFoundError(f"GEE key file not found: {key_file_path}")
            else:
                # Try user authentication (for development)
                ee.Initialize(project=self.project_id)
            
            self.initialized = True
            logger.info(f"Google Earth Engine initialized with project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"GEE initialization failed: {str(e)}")
            raise
    
    def create_roi_from_coordinates(self, coordinates: List[List[float]]) -> ee.Geometry:
        """Create region of interest from coordinates"""
        bbox = self._get_bounding_box(coordinates)
        return ee.Geometry.Rectangle([
            bbox["min_lon"], bbox["min_lat"],
            bbox["max_lon"], bbox["max_lat"]
        ])
    
    def _get_bounding_box(self, coordinates: List[List[float]]) -> Dict[str, float]:
        """Get bounding box from coordinates"""
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        return {
            "min_lon": min(lons),
            "max_lon": max(lons),
            "min_lat": min(lats),
            "max_lat": max(lats)
        }
    
    def get_urban_heat_island_data(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get Urban Heat Island data using Landsat surface temperature
        
        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for analysis
            
        Returns:
            Dictionary containing UHI analysis results
        """
        try:
            roi = self.create_roi_from_coordinates(coordinates)
            
            # Set default date range if not provided
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            
            # Get Landsat 9 collection for surface temperature
            landsat = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                      .filterBounds(roi)
                      .filterDate(date_range["start_date"], date_range["end_date"])
                      .filter(ee.Filter.lt("CLOUD_COVER", 20))
                      .median())
            
            # Calculate surface temperature (Kelvin to Celsius)
            lst = (landsat.select("ST_B10")
                   .multiply(0.00341802)
                   .add(149.0)
                   .subtract(273.15)
                   .rename("LST"))
            
            # Calculate NDVI for vegetation masking
            ndvi = landsat.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
            
            # Calculate NDBI for built-up areas
            ndbi = landsat.normalizedDifference(["SR_B6", "SR_B5"]).rename("NDBI")
            
            # Create composite image
            composite = ee.Image.cat([lst, ndvi, ndbi])
            
            # Get statistics for the region
            stats = composite.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            # Calculate UHI intensity (difference between urban and rural areas)
            urban_mask = ndbi.gt(0.2)  # Built-up areas
            rural_mask = ndbi.lt(-0.1).And(ndvi.gt(0.3))  # Rural/vegetated areas
            
            urban_temp = lst.updateMask(urban_mask).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            rural_temp = lst.updateMask(rural_mask).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            # Export task for visualization
            export_task = ee.batch.Export.image.toDrive(
                image=lst.clip(roi),
                description="UrbanHeat_Island_Analysis",
                folder="GEE_Urban_Analysis",
                fileNamePrefix="uhi_surface_temperature",
                region=roi.getInfo()["coordinates"],
                scale=30,
                crs="EPSG:4326"
            )
            
            # Start export task
            export_task.start()
            
            # Get computed values
            stats_info = stats.getInfo()
            urban_temp_info = urban_temp.getInfo()
            rural_temp_info = rural_temp.getInfo()
            
            # Calculate UHI intensity
            uhi_intensity = 0
            if urban_temp_info.get("LST") and rural_temp_info.get("LST"):
                uhi_intensity = urban_temp_info["LST"] - rural_temp_info["LST"]
            
            return {
                "surface_temperature": {
                    "mean": stats_info.get("LST_mean", 0),
                    "min": stats_info.get("LST_min", 0),
                    "max": stats_info.get("LST_max", 0),
                    "urban_mean": urban_temp_info.get("LST", 0),
                    "rural_mean": rural_temp_info.get("LST", 0)
                },
                "uhi_intensity": round(uhi_intensity, 2),
                "vegetation_index": {
                    "mean_ndvi": stats_info.get("NDVI_mean", 0),
                    "min_ndvi": stats_info.get("NDVI_min", 0),
                    "max_ndvi": stats_info.get("NDVI_max", 0)
                },
                "built_up_index": {
                    "mean_ndbi": stats_info.get("NDBI_mean", 0),
                    "min_ndbi": stats_info.get("NDBI_min", 0),
                    "max_ndbi": stats_info.get("NDBI_max", 0)
                },
                "export_task_id": export_task.id,
                "visualization_params": {
                    "lst": {"min": 20, "max": 40, "palette": ["blue", "yellow", "red"]},
                    "ndvi": {"min": 0, "max": 1, "palette": ["white", "green"]},
                    "ndbi": {"min": -0.2, "max": 0.3, "palette": ["blue", "white", "red"]}
                },
                "metadata": {
                    "date_range": date_range,
                    "satellite": "Landsat-9",
                    "resolution": "30m",
                    "analysis_type": "urban_heat_island"
                }
            }
            
        except Exception as e:
            logger.error(f"Urban Heat Island analysis failed: {str(e)}")
            raise
    
    def get_green_space_analysis(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze green space distribution and optimization opportunities
        
        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for analysis
            
        Returns:
            Dictionary containing green space analysis results
        """
        try:
            roi = self.create_roi_from_coordinates(coordinates)
            
            # Set default date range if not provided
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            
            # Get Landsat imagery for vegetation analysis
            landsat = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                      .filterBounds(roi)
                      .filterDate(date_range["start_date"], date_range["end_date"])
                      .filter(ee.Filter.lt("CLOUD_COVER", 20))
                      .median())
            
            # Calculate vegetation indices
            ndvi = landsat.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
            evi = (landsat.expression(
                '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                {
                    'NIR': landsat.select('SR_B5'),
                    'RED': landsat.select('SR_B4'),
                    'BLUE': landsat.select('SR_B2')
                }
            ).rename("EVI"))
            
            # Calculate land cover classification
            ndbi = landsat.normalizedDifference(["SR_B6", "SR_B5"]).rename("NDBI")
            
            # Define land cover classes
            vegetation = ndvi.gt(0.3)
            built_up = ndbi.gt(0.2)
            water = landsat.normalizedDifference(["SR_B3", "SR_B5"]).gt(0.1)
            bare_soil = ndvi.lt(0.2).And(ndbi.lt(0.1))
            
            # Create land cover classification
            land_cover = (vegetation.multiply(1)
                         .add(built_up.multiply(2))
                         .add(water.multiply(3))
                         .add(bare_soil.multiply(4))
                         .rename("LandCover"))
            
            # Calculate statistics
            stats = ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            # Calculate land cover percentages
            area_stats = land_cover.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            # Get population density (using WorldPop if available)
            try:
                population = (ee.ImageCollection("WorldPop/GP/100m/pop")
                            .filterDate("2020-01-01", "2020-12-31")
                            .mean()
                            .clip(roi))
                
                pop_stats = population.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=roi,
                    scale=100,
                    maxPixels=1e9
                )
                
                pop_density = pop_stats.getInfo().get("population", 0)
            except:
                pop_density = 1000  # Default value if WorldPop not available
            
            # Export vegetation map
            export_task = ee.batch.Export.image.toDrive(
                image=ndvi.clip(roi),
                description="GreenSpace_Analysis",
                folder="GEE_Urban_Analysis",
                fileNamePrefix="green_space_ndvi",
                region=roi.getInfo()["coordinates"],
                scale=30,
                crs="EPSG:4326"
            )
            export_task.start()
            
            # Get computed values
            stats_info = stats.getInfo()
            area_stats_info = area_stats.getInfo()
            
            # Calculate percentages
            total_pixels = sum(area_stats_info.get("LandCover", {}).values())
            land_cover_percentages = {}
            
            for class_id, count in area_stats_info.get("LandCover", {}).items():
                percentage = (count / total_pixels) * 100 if total_pixels > 0 else 0
                class_name = {1: "vegetation", 2: "built_up", 3: "water", 4: "bare_soil"}.get(int(class_id), "unknown")
                land_cover_percentages[class_name] = round(percentage, 2)
            
            # Calculate green space adequacy
            vegetation_percentage = land_cover_percentages.get("vegetation", 0)
            green_space_adequacy = "excellent" if vegetation_percentage > 30 else "adequate" if vegetation_percentage > 20 else "insufficient"
            
            # Generate optimization recommendations
            recommendations = []
            if vegetation_percentage < 20:
                recommendations.append({
                    "type": "increase_green_cover",
                    "priority": "high",
                    "description": "Current green space is below recommended 20%. Increase tree canopy and green infrastructure.",
                    "estimated_impact": "2-4°C temperature reduction",
                    "implementation_cost": "medium"
                })
            
            if pop_density > 5000 and vegetation_percentage < 25:
                recommendations.append({
                    "type": "high_density_green_spaces",
                    "priority": "high",
                    "description": "High population density area needs more green spaces for cooling and air quality.",
                    "estimated_impact": "Improved air quality, reduced heat stress",
                    "implementation_cost": "high"
                })
            
            return {
                "vegetation_analysis": {
                    "mean_ndvi": round(stats_info.get("NDVI_mean", 0), 3),
                    "min_ndvi": round(stats_info.get("NDVI_min", 0), 3),
                    "max_ndvi": round(stats_info.get("NDVI_max", 0), 3),
                    "vegetation_percentage": vegetation_percentage
                },
                "land_cover_distribution": land_cover_percentages,
                "green_space_assessment": {
                    "adequacy_level": green_space_adequacy,
                    "population_density": round(pop_density, 0),
                    "recommended_green_space": "30%",
                    "current_green_space": f"{vegetation_percentage:.1f}%"
                },
                "optimization_recommendations": recommendations,
                "export_task_id": export_task.id,
                "visualization_params": {
                    "ndvi": {"min": 0, "max": 1, "palette": ["white", "green"]},
                    "land_cover": {"min": 1, "max": 4, "palette": ["green", "red", "blue", "brown"]}
                },
                "metadata": {
                    "date_range": date_range,
                    "satellite": "Landsat-9",
                    "resolution": "30m",
                    "analysis_type": "green_space_optimization"
                }
            }
            
        except Exception as e:
            logger.error(f"Green space analysis failed: {str(e)}")
            raise
    
    def get_sustainable_building_zones(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sustainable building zones combining soil, water, and environmental data
        
        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for analysis
            
        Returns:
            Dictionary containing sustainable building zone analysis
        """
        try:
            roi = self.create_roi_from_coordinates(coordinates)
            
            # Set default date range if not provided
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            
            # Get elevation data (DEM)
            dem = ee.Image("USGS/SRTMGL1_003").clip(roi)
            
            # Calculate slope and aspect
            terrain = ee.Terrain.products(dem)
            slope = terrain.select('slope')
            
            # Get Landsat data for soil moisture and vegetation
            landsat = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                      .filterBounds(roi)
                      .filterDate(date_range["start_date"], date_range["end_date"])
                      .filter(ee.Filter.lt("CLOUD_COVER", 20))
                      .median())
            
            # Calculate soil moisture proxy (NDWI)
            ndwi = landsat.normalizedDifference(["SR_B3", "SR_B5"]).rename("NDWI")
            
            # Calculate vegetation health (NDVI)
            ndvi = landsat.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
            
            # Get Sentinel-5P NO2 data for air quality
            try:
                no2 = (ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2")
                      .select("NO2_column_number_density")
                      .filterBounds(roi)
                      .filterDate(date_range["start_date"], date_range["end_date"])
                      .mean())
                
                air_quality_available = True
            except:
                # Fallback if Sentinel-5P not available
                no2 = ee.Image.constant(0.0001).rename("NO2_column_number_density")
                air_quality_available = False
            
            # Create composite for analysis
            composite = ee.Image.cat([dem, slope, ndwi, ndvi, no2])
            
            # Calculate statistics
            stats = composite.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            # Define suitability criteria
            # Low slope (< 15 degrees) for construction
            slope_suitable = slope.lt(15)
            
            # Moderate elevation (avoid flood zones and high mountains)
            elevation_suitable = dem.gt(5).And(dem.lt(500))
            
            # Good soil moisture (not too wet, not too dry)
            soil_suitable = ndwi.gt(-0.1).And(ndwi.lt(0.3))
            
            # Existing vegetation (not completely bare)
            vegetation_suitable = ndvi.gt(0.1)
            
            # Good air quality (low NO2)
            air_quality_suitable = no2.lt(0.0002) if air_quality_available else ee.Image.constant(1)
            
            # Combine all criteria
            suitability_score = (slope_suitable.multiply(0.25)
                               .add(elevation_suitable.multiply(0.25))
                               .add(soil_suitable.multiply(0.2))
                               .add(vegetation_suitable.multiply(0.15))
                               .add(air_quality_suitable.multiply(0.15)))
            
            # Classify zones
            building_zones = suitability_score.gte(0.7).rename("BuildingZones")
            
            # Calculate flood risk (low elevation + high moisture)
            flood_risk = ndwi.gt(0.2).And(dem.lt(10)).rename("FloodRisk")
            
            # Calculate erosion risk (high slope + low vegetation)
            erosion_risk = slope.gt(20).And(ndvi.lt(0.2)).rename("ErosionRisk")
            
            # Export suitability map
            export_task = ee.batch.Export.image.toDrive(
                image=suitability_score.clip(roi),
                description="SustainableBuildingZones",
                folder="GEE_Urban_Analysis",
                fileNamePrefix="building_suitability",
                region=roi.getInfo()["coordinates"],
                scale=30,
                crs="EPSG:4326"
            )
            export_task.start()
            
            # Get computed values
            stats_info = stats.getInfo()
            
            # Calculate zone percentages
            zone_stats = building_zones.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            risk_stats = ee.Image.cat([flood_risk, erosion_risk]).reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            zone_info = zone_stats.getInfo()
            risk_info = risk_stats.getInfo()
            
            # Calculate percentages
            total_pixels = sum(zone_info.get("BuildingZones", {}).values())
            suitable_pixels = zone_info.get("BuildingZones", {}).get("1", 0)
            suitability_percentage = (suitable_pixels / total_pixels * 100) if total_pixels > 0 else 0
            
            flood_pixels = risk_info.get("FloodRisk", {}).get("1", 0)
            flood_risk_percentage = (flood_pixels / total_pixels * 100) if total_pixels > 0 else 0
            
            erosion_pixels = risk_info.get("ErosionRisk", {}).get("1", 0)
            erosion_risk_percentage = (erosion_pixels / total_pixels * 100) if total_pixels > 0 else 0
            
            # Generate recommendations
            recommendations = []
            
            if suitability_percentage < 30:
                recommendations.append({
                    "type": "limited_suitable_areas",
                    "priority": "high",
                    "description": "Limited suitable areas for construction. Consider soil improvement and slope stabilization.",
                    "estimated_impact": "Reduced construction costs, improved stability",
                    "implementation_cost": "high"
                })
            
            if flood_risk_percentage > 20:
                recommendations.append({
                    "type": "flood_mitigation",
                    "priority": "high",
                    "description": "High flood risk areas detected. Implement drainage systems and elevation strategies.",
                    "estimated_impact": "Reduced flood damage, improved safety",
                    "implementation_cost": "high"
                })
            
            if erosion_risk_percentage > 15:
                recommendations.append({
                    "type": "erosion_control",
                    "priority": "medium",
                    "description": "Erosion risk areas identified. Implement vegetation cover and slope stabilization.",
                    "estimated_impact": "Reduced soil erosion, improved stability",
                    "implementation_cost": "medium"
                })
            
            return {
                "terrain_analysis": {
                    "mean_elevation": round(stats_info.get("elevation_mean", 0), 1),
                    "min_elevation": round(stats_info.get("elevation_min", 0), 1),
                    "max_elevation": round(stats_info.get("elevation_max", 0), 1),
                    "mean_slope": round(stats_info.get("slope_mean", 0), 1),
                    "max_slope": round(stats_info.get("slope_max", 0), 1)
                },
                "soil_water_analysis": {
                    "mean_soil_moisture": round(stats_info.get("NDWI_mean", 0), 3),
                    "min_soil_moisture": round(stats_info.get("NDWI_min", 0), 3),
                    "max_soil_moisture": round(stats_info.get("NDWI_max", 0), 3),
                    "mean_vegetation": round(stats_info.get("NDVI_mean", 0), 3)
                },
                "air_quality_analysis": {
                    "mean_no2": round(stats_info.get("NO2_column_number_density_mean", 0), 6),
                    "air_quality_available": air_quality_available,
                    "air_quality_rating": "good" if stats_info.get("NO2_column_number_density_mean", 0) < 0.0001 else "moderate"
                },
                "suitability_assessment": {
                    "suitable_for_construction": round(suitability_percentage, 1),
                    "flood_risk_percentage": round(flood_risk_percentage, 1),
                    "erosion_risk_percentage": round(erosion_risk_percentage, 1),
                    "overall_suitability": "excellent" if suitability_percentage > 60 else "good" if suitability_percentage > 40 else "fair" if suitability_percentage > 20 else "poor"
                },
                "recommendations": recommendations,
                "export_task_id": export_task.id,
                "visualization_params": {
                    "suitability": {"min": 0, "max": 1, "palette": ["red", "yellow", "green"]},
                    "flood_risk": {"min": 0, "max": 1, "palette": ["blue", "red"]},
                    "erosion_risk": {"min": 0, "max": 1, "palette": ["brown", "red"]}
                },
                "metadata": {
                    "date_range": date_range,
                    "satellites": ["Landsat-9", "Sentinel-5P", "SRTM"],
                    "resolution": "30m",
                    "analysis_type": "sustainable_building_zones"
                }
            }
            
        except Exception as e:
            logger.error(f"Sustainable building zones analysis failed: {str(e)}")
            raise
    
    def get_comprehensive_analysis(
        self,
        coordinates: List[List[float]],
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive urban analysis combining all three analyses
        
        Args:
            coordinates: Bounding box coordinates
            date_range: Date range for analysis
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        try:
            # Run all three analyses
            uhi_results = self.get_urban_heat_island_data(coordinates, date_range)
            green_space_results = self.get_green_space_analysis(coordinates, date_range)
            building_zones_results = self.get_sustainable_building_zones(coordinates, date_range)
            
            # Combine results
            comprehensive_analysis = {
                "urban_heat_island": uhi_results,
                "green_space_optimization": green_space_results,
                "sustainable_building_zones": building_zones_results,
                "summary": {
                    "analysis_area": coordinates,
                    "date_range": date_range or {
                        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d")
                    },
                    "total_export_tasks": 3,
                    "data_sources": ["Landsat-9", "Sentinel-5P", "SRTM", "WorldPop"],
                    "analysis_completed_at": datetime.now().isoformat()
                }
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {str(e)}")
            raise
    
    def check_export_status(self, task_id: str) -> Dict[str, Any]:
        """Check the status of an export task"""
        try:
            # Get task status from GEE
            tasks = ee.batch.Task.list()
            for task in tasks:
                if task.id == task_id:
                    return {
                        "task_id": task_id,
                        "state": task.state,
                        "creation_timestamp": task.creation_timestamp,
                        "start_timestamp": task.start_timestamp,
                        "update_timestamp": task.update_timestamp,
                        "description": task.description
                    }
            
            return {"task_id": task_id, "state": "not_found"}
            
        except Exception as e:
            logger.error(f"Failed to check export status: {str(e)}")
            return {"task_id": task_id, "state": "error", "error": str(e)}
