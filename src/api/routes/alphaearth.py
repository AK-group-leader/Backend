"""
AlphaEarth-specific API routes for environmental data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from src.data_ingestion.alphaearth_ingestion import AlphaEarthDataIngestion
from src.databricks_integration.delta_lake import delta_lake_manager
from src.utils.validators import validate_coordinates, validate_area_bounds
from src.utils.geospatial import GeospatialProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


class AlphaEarthRequest(BaseModel):
    """Request model for AlphaEarth data"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates for data extraction",
        example=[[-74.0059, 40.7128], [-74.0059, 40.7589],
                 [-73.9352, 40.7589], [-73.9352, 40.7128]]
    )
    data_types: Optional[List[str]] = Field(
        default=["satellite", "soil", "water", "climate"],
        description="Types of data to retrieve from AlphaEarth"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for data extraction"
    )
    resolution: str = Field(
        default="high",
        description="Data resolution",
        enum=["low", "medium", "high", "ultra"]
    )
    # Additional fields for frontend compatibility
    satellite_type: Optional[str] = Field(
        default="landsat",
        description="Type of satellite data",
        enum=["landsat", "sentinel", "modis"]
    )
    bands: Optional[List[str]] = Field(
        default=["red", "green", "blue", "nir"],
        description="Satellite bands to retrieve"
    )
    date: Optional[str] = Field(
        default=None,
        description="Specific date for data extraction (YYYY-MM-DD)"
    )
    cloud_coverage: Optional[float] = Field(
        default=0.1,
        description="Maximum cloud coverage threshold",
        ge=0.0,
        le=1.0
    )


class HeatmapRequest(BaseModel):
    """Request model for heatmap generation"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates"
    )
    data_type: str = Field(
        ...,
        description="Type of heatmap to generate",
        enum=["temperature", "air_quality",
              "water_absorption", "vegetation", "urban_heat"]
    )
    resolution: int = Field(
        default=100,
        description="Heatmap resolution",
        ge=50,
        le=1000
    )


class SustainabilityScoreRequest(BaseModel):
    """Request model for sustainability scoring"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Analysis area coordinates"
    )
    development_scenario: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Proposed development scenario"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include sustainability recommendations"
    )


@router.post("/satellite-data")
async def get_satellite_data(
    request: AlphaEarthRequest,
    background_tasks: BackgroundTasks
):
    """
    Get satellite data from AlphaEarth API
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        if not validate_area_bounds(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Analysis area too large. Maximum 100 km² allowed"
            )

        # Handle date range - convert frontend date format to date_range
        date_range = request.date_range
        if request.date and not date_range:
            date_range = {
                "start_date": request.date,
                "end_date": request.date
            }

        # Get satellite data from AlphaEarth
        ingester = AlphaEarthDataIngestion()
        result = await ingester.ingest_satellite_data(
            coordinates=request.coordinates,
            date_range=date_range,
            resolution=request.resolution
        )

        # Check if we got an error response
        if "error" in result:
            error_message = result['error']
            # Provide more specific error messages
            if "Empty date ranges not supported" in error_message:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date range provided. Please ensure start_date is before end_date and there's at least a 1-day difference."
                )
            elif "No Landsat images available" in error_message:
                raise HTTPException(
                    status_code=404,
                    detail="No satellite imagery available for the specified coordinates and date range. Try expanding the date range or selecting a different area."
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Satellite data unavailable: {error_message}"
                )

        # Process satellite data
        satellite_data = result.get("satellite_data", {})

        if not satellite_data:
            raise HTTPException(
                status_code=404,
                detail="No satellite data found for the specified coordinates and date range"
            )

        return {
            "satellite_data": {
                "image_url": satellite_data.get("image_url"),
                "metadata": {
                    "satellite": satellite_data.get("satellite", request.satellite_type.title()),
                    "acquisition_date": satellite_data.get("acquisition_date"),
                    "resolution": satellite_data.get("resolution"),
                    "cloud_coverage": satellite_data.get("cloud_coverage"),
                    "sun_elevation": satellite_data.get("sun_elevation"),
                    "sun_azimuth": satellite_data.get("sun_azimuth"),
                    "satellite_type": request.satellite_type,
                    "bands": request.bands,
                    "bounds": {
                        "north": max(coord[1] for coord in request.coordinates),
                        "south": min(coord[1] for coord in request.coordinates),
                        "east": max(coord[0] for coord in request.coordinates),
                        "west": min(coord[0] for coord in request.coordinates)
                    }
                },
                "indices": {
                    "ndvi": satellite_data.get("ndvi"),
                    "ndwi": satellite_data.get("ndwi"),
                    "ndbi": satellite_data.get("ndbi"),
                    "surface_temperature": satellite_data.get("surface_temperature")
                },
                "land_cover": {
                    "vegetation": satellite_data.get("vegetation_percentage"),
                    "urban": satellite_data.get("urban_percentage"),
                    "water": satellite_data.get("water_percentage"),
                    "bare_soil": satellite_data.get("bare_soil_percentage")
                }
            },
            "processing_info": {
                "processing_time": result.get("metadata", {}).get("processing_time", "unknown"),
                "algorithms_used": ["ndvi", "land_cover_classification"],
                "confidence": result.get("metadata", {}).get("confidence", 0.0)
            },
            "coordinates": request.coordinates,
            "data_source": result.get("metadata", {}).get("data_source", "unknown"),
            "request_info": {
                "satellite_type": request.satellite_type,
                "bands": request.bands,
                "date": request.date,
                "cloud_coverage": request.cloud_coverage
            },
            "records_ingested": result.get("records_ingested", 0)
        }

    except Exception as e:
        logger.error(f"Satellite data retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Satellite data retrieval failed: {str(e)}"
        )


@router.post("/soil-data")
async def get_soil_data(
    request: AlphaEarthRequest,
    background_tasks: BackgroundTasks
):
    """
    Get soil data from AlphaEarth API
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Get soil data from AlphaEarth
        ingester = AlphaEarthDataIngestion()
        result = await ingester.ingest_soil_data(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        # Check if we got an error response
        if "error" in result:
            raise HTTPException(
                status_code=503,
                detail=f"Soil data unavailable: {result['error']}"
            )

        soil_data = result.get("soil_data", {})

        if not soil_data:
            raise HTTPException(
                status_code=404,
                detail="No soil data found for the specified coordinates"
            )

        return {
            "soil_data": {
                "composition": {
                    "sand": soil_data.get("sand_percentage", 45.0),
                    "silt": soil_data.get("silt_percentage", 35.0),
                    "clay": soil_data.get("clay_percentage", 20.0),
                    "organic_matter": soil_data.get("organic_matter_percentage", 5.0)
                },
                "properties": {
                    "ph": soil_data.get("ph", 6.8),
                    "moisture_content": soil_data.get("moisture_content", 0.25),
                    "bulk_density": soil_data.get("bulk_density", 1.35),
                    "permeability": soil_data.get("permeability", 0.6)
                },
                "nutrients": {
                    "nitrogen": soil_data.get("nitrogen_content", 0.15),
                    "phosphorus": soil_data.get("phosphorus_content", 0.08),
                    "potassium": soil_data.get("potassium_content", 0.12)
                }
            },
            "coordinates": request.coordinates,
            "data_source": "alphaearth"
        }

    except Exception as e:
        logger.error(f"Soil data retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Soil data retrieval failed: {str(e)}"
        )


@router.post("/water-data")
async def get_water_data(
    request: AlphaEarthRequest,
    background_tasks: BackgroundTasks
):
    """
    Get water data from AlphaEarth API
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Get water data from AlphaEarth
        ingester = AlphaEarthDataIngestion()
        result = await ingester.ingest_water_data(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        water_data = result.get("water_data", {})

        return {
            "water_data": {
                "quality": {
                    "ph": water_data.get("ph", 7.2),
                    "dissolved_oxygen": water_data.get("dissolved_oxygen", 8.5),
                    "turbidity": water_data.get("turbidity", 2.1),
                    "total_solids": water_data.get("total_solids", 150.0)
                },
                "contaminants": {
                    "nitrates": water_data.get("nitrates", 0.5),
                    "phosphates": water_data.get("phosphates", 0.1),
                    "heavy_metals": water_data.get("heavy_metals", 0.02),
                    "bacteria": water_data.get("bacteria", "low")
                },
                "availability": {
                    "groundwater_depth": water_data.get("groundwater_depth", 15.5),
                    "surface_water_presence": water_data.get("surface_water_presence", True),
                    "water_stress_index": water_data.get("water_stress_index", 0.3)
                }
            },
            "coordinates": request.coordinates,
            "data_source": "alphaearth"
        }

    except Exception as e:
        logger.error(f"Water data retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Water data retrieval failed: {str(e)}"
        )


@router.post("/climate-data")
async def get_climate_data(
    request: AlphaEarthRequest,
    background_tasks: BackgroundTasks
):
    """
    Get climate data from AlphaEarth API
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Get climate data from AlphaEarth
        ingester = AlphaEarthDataIngestion()
        result = await ingester.ingest_climate_data(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        climate_data = result.get("climate_data", {})

        return {
            "climate_data": {
                "current_conditions": {
                    "temperature": climate_data.get("temperature", 22.5),
                    "humidity": climate_data.get("humidity", 65.0),
                    "pressure": climate_data.get("pressure", 1013.25),
                    "wind_speed": climate_data.get("wind_speed", 5.2),
                    "wind_direction": climate_data.get("wind_direction", 225.0)
                },
                "precipitation": {
                    "daily": climate_data.get("daily_precipitation", 2.5),
                    "monthly": climate_data.get("monthly_precipitation", 75.0),
                    "annual": climate_data.get("annual_precipitation", 900.0)
                },
                "trends": {
                    "temperature_trend": climate_data.get("temperature_trend", 0.02),
                    "precipitation_trend": climate_data.get("precipitation_trend", -0.01),
                    "climate_zone": climate_data.get("climate_zone", "temperate")
                }
            },
            "coordinates": request.coordinates,
            "data_source": "alphaearth"
        }

    except Exception as e:
        logger.error(f"Climate data retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Climate data retrieval failed: {str(e)}"
        )


@router.post("/data/ingest")
async def ingest_alphaearth_data(
    request: AlphaEarthRequest,
    background_tasks: BackgroundTasks
):
    """
    Ingest data from AlphaEarth API and store in Delta Lake
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        if not validate_area_bounds(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Analysis area too large. Maximum 100 km² allowed"
            )

        # Ingest data from AlphaEarth
        ingester = AlphaEarthDataIngestion()
        result = await ingester.ingest_data(
            coordinates=request.coordinates,
            date_range=request.date_range,
            data_types=request.data_types
        )

        # Process and store in Delta Lake
        processed_tables = []
        if result.get("alphaearth_data"):
            for data_type, data in result["alphaearth_data"].items():
                try:
                    if data_type == "satellite":
                        processed_data = await delta_lake_manager.process_satellite_data(
                            data, request.coordinates
                        )
                        table_name = await delta_lake_manager.store_alphaearth_data(
                            "satellite_processed", processed_data, request.coordinates
                        )
                    elif data_type == "soil":
                        processed_data = await delta_lake_manager.process_soil_data(
                            data, request.coordinates
                        )
                        table_name = await delta_lake_manager.store_alphaearth_data(
                            "soil_processed", processed_data, request.coordinates
                        )
                    elif data_type == "climate":
                        processed_data = await delta_lake_manager.process_climate_data(
                            data, request.coordinates
                        )
                        table_name = await delta_lake_manager.store_alphaearth_data(
                            "climate_processed", processed_data, request.coordinates
                        )
                    else:
                        table_name = await delta_lake_manager.store_alphaearth_data(
                            data_type, data, request.coordinates
                        )

                    if table_name:
                        processed_tables.append(table_name)

                except Exception as e:
                    logger.error(
                        f"Failed to process {data_type} data: {str(e)}")
                    continue

        return {
            "ingestion_id": f"alphaearth_{hash(str(request.coordinates))}",
            "status": "completed",
            "records_ingested": result.get("records_ingested", 0),
            "data_types": request.data_types,
            "processed_tables": processed_tables,
            "coordinates": request.coordinates,
            "metadata": {
                "resolution": request.resolution,
                "date_range": request.date_range,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

    except Exception as e:
        logger.error(f"AlphaEarth data ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data ingestion failed: {str(e)}"
        )


@router.post("/heatmap")
async def generate_alphaearth_heatmap(request: HeatmapRequest):
    """
    Generate heatmap using AlphaEarth data
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Get processed data from Delta Lake
        data_type_mapping = {
            "temperature": "satellite_processed",
            "air_quality": "climate_processed",
            "water_absorption": "soil_processed",
            "vegetation": "satellite_processed",
            "urban_heat": "satellite_processed"
        }

        source_data_type = data_type_mapping.get(
            request.data_type, "satellite_processed")

        try:
            processed_data = await delta_lake_manager.get_processed_data(
                data_type=source_data_type,
                coordinates=request.coordinates
            )
        except Exception as e:
            logger.warning(f"Could not retrieve processed data: {str(e)}")
            processed_data = []

        # Generate heatmap data
        if processed_data:
            # Use real AlphaEarth data
            heatmap_data = await _generate_heatmap_from_alphaearth_data(
                processed_data[0], request.data_type, request.coordinates, request.resolution
            )
        else:
            # Fallback to placeholder data
            heatmap_data = await _generate_placeholder_heatmap(
                request.data_type, request.coordinates, request.resolution
            )

        return {
            "heatmap_id": f"alphaearth_{request.data_type}_{hash(str(request.coordinates))}",
            "data_type": request.data_type,
            "coordinates": request.coordinates,
            "resolution": request.resolution,
            "heatmap_data": heatmap_data,
            "data_source": "alphaearth",
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "has_real_data": len(processed_data) > 0
            }
        }

    except Exception as e:
        logger.error(f"Heatmap generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Heatmap generation failed: {str(e)}"
        )


@router.post("/sustainability-score")
async def calculate_sustainability_score(request: SustainabilityScoreRequest):
    """
    Calculate sustainability score using AlphaEarth data
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Get AlphaEarth data
        alphaearth_data = {}
        data_types = ["satellite_processed",
                      "soil_processed", "climate_processed"]

        for data_type in data_types:
            try:
                data = await delta_lake_manager.get_processed_data(
                    data_type=data_type,
                    coordinates=request.coordinates
                )
                if data:
                    alphaearth_data[data_type] = data[0]
            except Exception as e:
                logger.warning(f"Could not retrieve {data_type}: {str(e)}")
                continue

        # Calculate sustainability score
        sustainability_score = await _calculate_sustainability_score(
            alphaearth_data, request.coordinates, request.development_scenario
        )

        # Generate recommendations if requested
        recommendations = []
        if request.include_recommendations:
            recommendations = await _generate_sustainability_recommendations(
                sustainability_score, alphaearth_data
            )

        return {
            "sustainability_id": f"sustainability_{hash(str(request.coordinates))}",
            "coordinates": request.coordinates,
            "sustainability_score": sustainability_score,
            "recommendations": recommendations,
            "data_source": "alphaearth",
            "metadata": {
                "calculated_at": "2024-01-01T00:00:00Z",
                "has_real_data": len(alphaearth_data) > 0,
                "development_scenario": request.development_scenario
            }
        }

    except Exception as e:
        logger.error(f"Sustainability score calculation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Sustainability score calculation failed: {str(e)}"
        )


@router.post("/city-data")
async def get_comprehensive_city_data(
    request: AlphaEarthRequest,
    background_tasks: BackgroundTasks
):
    """
    Get comprehensive city data for urban planning and temperature reduction analysis

    This endpoint combines satellite, soil, water, climate, and building data
    to provide insights for urban planning and reducing city temperatures.
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        if not validate_area_bounds(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Analysis area too large. Maximum 100 km² allowed"
            )

        # Get all data types in parallel
        ingester = AlphaEarthDataIngestion()

        # Prepare date range
        date_range = request.date_range
        if request.date and not date_range:
            date_range = {
                "start_date": request.date,
                "end_date": request.date
            }

        # Collect all data types
        city_data = {}
        data_tasks = []

        # Satellite data (vegetation, buildings, land cover)
        data_tasks.append(("satellite", ingester.ingest_satellite_data(
            coordinates=request.coordinates,
            date_range=date_range,
            resolution=request.resolution
        )))

        # Soil data (water absorption, composition)
        data_tasks.append(("soil", ingester.ingest_soil_data(
            coordinates=request.coordinates,
            date_range=date_range
        )))

        # Water data (water bodies, quality)
        data_tasks.append(("water", ingester.ingest_water_data(
            coordinates=request.coordinates,
            date_range=date_range
        )))

        # Climate data (temperature, humidity, wind)
        data_tasks.append(("climate", ingester.ingest_climate_data(
            coordinates=request.coordinates,
            date_range=date_range
        )))

        # Execute all data collection tasks
        for data_type, task in data_tasks:
            try:
                result = await task
                city_data[data_type] = result
            except Exception as e:
                logger.warning(f"Failed to get {data_type} data: {str(e)}")
                city_data[data_type] = {"error": str(e)}

        # Process and analyze the data
        analysis_results = await _analyze_city_data(city_data, request.coordinates)

        return {
            "city_id": f"city_{hash(str(request.coordinates))}",
            "coordinates": request.coordinates,
            "data_sources": {
                "satellite": "alphaearth_gee" if not ingester.mock_mode else "mock",
                "soil": "alphaearth_gee" if not ingester.mock_mode else "mock",
                "water": "alphaearth_gee" if not ingester.mock_mode else "mock",
                "climate": "alphaearth_gee" if not ingester.mock_mode else "mock"
            },
            "urban_planning_insights": analysis_results["urban_planning"],
            "temperature_analysis": analysis_results["temperature"],
            "environmental_metrics": analysis_results["environmental"],
            "recommendations": analysis_results["recommendations"],
            "raw_data": city_data,
            "metadata": {
                "analysis_date": "2024-01-01T00:00:00Z",
                "data_quality": "high" if not ingester.mock_mode else "mock",
                "resolution": request.resolution,
                "area_km2": analysis_results["area_km2"]
            }
        }

    except Exception as e:
        logger.error(f"City data retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"City data retrieval failed: {str(e)}"
        )


@router.get("/data/status")
async def get_alphaearth_data_status():
    """
    Get status of AlphaEarth data in the system
    """
    try:
        # TODO: Implement actual status checking
        return {
            "status": "active",
            "data_sources": {
                "satellite": "available",
                "soil": "available",
                "water": "available",
                "climate": "available",
                "vegetation": "available"
            },
            "last_updated": "2024-01-01T00:00:00Z",
            "coverage": "global"
        }

    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )


# Helper functions
async def _generate_heatmap_from_alphaearth_data(
    processed_data: Dict[str, Any],
    data_type: str,
    coordinates: List[List[float]],
    resolution: int
) -> Dict[str, Any]:
    """Generate heatmap from real AlphaEarth data"""
    try:
        # TODO: Implement actual heatmap generation from AlphaEarth data
        # This would extract the relevant data fields and create a proper heatmap

        if data_type == "temperature":
            # Extract temperature data from satellite processing
            temperature_data = processed_data.get(
                "data", {}).get("surface_temperature", 25.0)
            return {
                "temperature": temperature_data,
                "data_source": "alphaearth_satellite"
            }
        elif data_type == "vegetation":
            # Extract NDVI data
            ndvi_data = processed_data.get("data", {}).get("ndvi", 0.5)
            return {
                "ndvi": ndvi_data,
                "vegetation_density": processed_data.get("data", {}).get("vegetation_density", 0.4),
                "data_source": "alphaearth_satellite"
            }
        elif data_type == "water_absorption":
            # Extract soil permeability data
            permeability = processed_data.get(
                "data", {}).get("permeability", 0.6)
            return {
                "permeability": permeability,
                "water_holding_capacity": processed_data.get("data", {}).get("water_holding_capacity", 0.7),
                "data_source": "alphaearth_soil"
            }
        else:
            # Default fallback
            return {
                "value": 0.5,
                "data_source": "alphaearth"
            }

    except Exception as e:
        logger.error(
            f"Heatmap generation from AlphaEarth data failed: {str(e)}")
        return {"value": 0.5, "data_source": "alphaearth_fallback"}


async def _generate_placeholder_heatmap(
    data_type: str,
    coordinates: List[List[float]],
    resolution: int
) -> Dict[str, Any]:
    """Generate placeholder heatmap when no real data is available"""
    import numpy as np

    # Generate grid points
    bbox = _get_bounding_box(coordinates)
    lons = np.linspace(bbox["min_lon"], bbox["max_lon"], resolution)
    lats = np.linspace(bbox["min_lat"], bbox["max_lat"], resolution)

    # Generate placeholder data based on type
    if data_type == "temperature":
        data = np.random.normal(25, 5, (resolution, resolution))
    elif data_type == "vegetation":
        data = np.random.uniform(0.2, 0.8, (resolution, resolution))
    elif data_type == "water_absorption":
        data = np.random.uniform(0.3, 0.9, (resolution, resolution))
    else:
        data = np.random.uniform(0, 1, (resolution, resolution))

    return {
        "data": data.tolist(),
        "lons": lons.tolist(),
        "lats": lats.tolist(),
        "data_source": "placeholder"
    }


async def _calculate_sustainability_score(
    alphaearth_data: Dict[str, Any],
    coordinates: List[List[float]],
    development_scenario: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate sustainability score using AlphaEarth data"""
    try:
        # TODO: Implement actual sustainability scoring algorithm
        # This would use the AlphaEarth data to calculate various sustainability metrics

        score_components = {
            "environmental_health": 0.7,
            "resource_efficiency": 0.6,
            "climate_resilience": 0.8,
            "biodiversity": 0.5,
            "social_equity": 0.6
        }

        # Adjust scores based on AlphaEarth data if available
        if "satellite_processed" in alphaearth_data:
            satellite_data = alphaearth_data["satellite_processed"]
            ndvi = satellite_data.get("data", {}).get("ndvi", 0.5)
            score_components["biodiversity"] = min(ndvi * 1.2, 1.0)

        if "soil_processed" in alphaearth_data:
            soil_data = alphaearth_data["soil_processed"]
            permeability = soil_data.get("data", {}).get("permeability", 0.6)
            score_components["resource_efficiency"] = min(
                permeability * 1.1, 1.0)

        # Calculate overall score
        overall_score = sum(score_components.values()) / len(score_components)

        return {
            "overall_score": round(overall_score, 3),
            "components": score_components,
            "grade": _get_sustainability_grade(overall_score),
            "data_quality": "high" if len(alphaearth_data) > 0 else "low"
        }

    except Exception as e:
        logger.error(f"Sustainability score calculation failed: {str(e)}")
        return {
            "overall_score": 0.5,
            "components": {},
            "grade": "C",
            "data_quality": "unknown"
        }


async def _generate_sustainability_recommendations(
    sustainability_score: Dict[str, Any],
    alphaearth_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate sustainability recommendations based on AlphaEarth data"""
    try:
        recommendations = []

        overall_score = sustainability_score.get("overall_score", 0.5)
        components = sustainability_score.get("components", {})

        # Generate recommendations based on low-scoring components
        for component, score in components.items():
            if score < 0.6:
                if component == "biodiversity":
                    recommendations.append({
                        "type": "vegetation",
                        "title": "Increase Green Infrastructure",
                        "description": "Plant more trees and create green spaces to improve biodiversity",
                        "impact": "High",
                        "cost": "Medium",
                        "priority": 1
                    })
                elif component == "resource_efficiency":
                    recommendations.append({
                        "type": "water_management",
                        "title": "Improve Water Management",
                        "description": "Implement rainwater harvesting and permeable surfaces",
                        "impact": "High",
                        "cost": "High",
                        "priority": 1
                    })
                elif component == "climate_resilience":
                    recommendations.append({
                        "type": "climate_adaptation",
                        "title": "Enhance Climate Resilience",
                        "description": "Implement climate adaptation measures and heat mitigation strategies",
                        "impact": "High",
                        "cost": "High",
                        "priority": 1
                    })

        return recommendations

    except Exception as e:
        logger.error(f"Recommendation generation failed: {str(e)}")
        return []


def _get_sustainability_grade(score: float) -> str:
    """Convert sustainability score to letter grade"""
    if score >= 0.9:
        return "A+"
    elif score >= 0.8:
        return "A"
    elif score >= 0.7:
        return "B+"
    elif score >= 0.6:
        return "B"
    elif score >= 0.5:
        return "C"
    elif score >= 0.4:
        return "D"
    else:
        return "F"


async def _analyze_city_data(city_data: Dict[str, Any], coordinates: List[List[float]]) -> Dict[str, Any]:
    """Analyze comprehensive city data for urban planning insights"""
    try:
        # Calculate area
        geospatial_processor = GeospatialProcessor()
        area_km2 = geospatial_processor.calculate_area_km2(coordinates)

        # Extract data from each source
        satellite_data = city_data.get(
            "satellite", {}).get("satellite_data", {})
        soil_data = city_data.get("soil", {}).get("soil_data", {})
        water_data = city_data.get("water", {}).get("water_data", {})
        climate_data = city_data.get("climate", {}).get("climate_data", {})

        # Urban Planning Insights
        urban_planning = {
            "land_use_distribution": {
                "vegetation_percentage": satellite_data.get("vegetation_percentage", 0.3),
                "urban_percentage": satellite_data.get("urban_percentage", 0.4),
                "water_percentage": satellite_data.get("water_percentage", 0.1),
                "bare_soil_percentage": satellite_data.get("bare_soil_percentage", 0.2)
            },
            "infrastructure_assessment": {
                "green_space_adequacy": "adequate" if satellite_data.get("vegetation_percentage", 0) > 0.25 else "insufficient",
                "water_body_presence": "present" if satellite_data.get("water_percentage", 0) > 0.05 else "limited",
                "development_density": "high" if satellite_data.get("urban_percentage", 0) > 0.5 else "moderate"
            },
            "planning_recommendations": []
        }

        # Temperature Analysis
        temperature_analysis = {
            "current_temperature": climate_data.get("temperature", 22.5),
            "surface_temperature": satellite_data.get("surface_temperature", 28.5),
            "heat_island_effect": "moderate" if satellite_data.get("surface_temperature", 25) > climate_data.get("temperature", 20) + 3 else "minimal",
            "cooling_potential": {
                # °C reduction potential
                "vegetation_cooling": satellite_data.get("vegetation_percentage", 0.3) * 2.5,
                "water_cooling": satellite_data.get("water_percentage", 0.1) * 1.8,
                "total_cooling_potential": (satellite_data.get("vegetation_percentage", 0.3) * 2.5) +
                (satellite_data.get("water_percentage", 0.1) * 1.8)
            }
        }

        # Environmental Metrics
        environmental_metrics = {
            "air_quality_index": 75,  # Would be calculated from actual air quality data
            "water_quality_score": 8.2,  # Would be calculated from water data
            "soil_health": {
                "organic_matter": soil_data.get("organic_matter_percentage", 5.0),
                "permeability": soil_data.get("permeability", 0.6),
                "ph_level": soil_data.get("ph", 6.8)
            },
            "biodiversity_index": satellite_data.get("ndvi", 0.65) * 100,
            "carbon_sequestration_potential": satellite_data.get("vegetation_percentage", 0.3) * 0.8
        }

        # Generate Recommendations
        recommendations = []

        # Vegetation recommendations
        if satellite_data.get("vegetation_percentage", 0) < 0.25:
            recommendations.append({
                "category": "green_infrastructure",
                "priority": "high",
                "title": "Increase Green Cover",
                "description": "Current vegetation cover is below recommended 25%. Increase tree canopy and green spaces.",
                "estimated_impact": "2-4°C temperature reduction",
                "implementation_cost": "medium"
            })

        # Water management recommendations
        if satellite_data.get("water_percentage", 0) < 0.1:
            recommendations.append({
                "category": "water_management",
                "priority": "medium",
                "title": "Enhance Water Features",
                "description": "Consider adding water features, rain gardens, or permeable surfaces for cooling.",
                "estimated_impact": "1-2°C temperature reduction",
                "implementation_cost": "high"
            })

        # Soil recommendations
        if soil_data.get("permeability", 1) < 0.5:
            recommendations.append({
                "category": "soil_management",
                "priority": "medium",
                "title": "Improve Soil Permeability",
                "description": "Enhance soil drainage and water absorption capacity.",
                "estimated_impact": "Reduced flooding, better water management",
                "implementation_cost": "low"
            })

        return {
            "urban_planning": urban_planning,
            "temperature": temperature_analysis,
            "environmental": environmental_metrics,
            "recommendations": recommendations,
            "area_km2": area_km2
        }

    except Exception as e:
        logger.error(f"City data analysis failed: {str(e)}")
        return {
            "urban_planning": {},
            "temperature": {},
            "environmental": {},
            "recommendations": [],
            "area_km2": 0.0
        }


def _get_bounding_box(coordinates: List[List[float]]) -> Dict[str, float]:
    """Get bounding box from coordinates"""
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]

    return {
        "min_lon": min(lons),
        "max_lon": max(lons),
        "min_lat": min(lats),
        "max_lat": max(lats)
    }
