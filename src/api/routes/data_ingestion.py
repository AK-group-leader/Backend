"""
Data ingestion API routes for external data sources
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from src.data_ingestion.alphaearth_ingestion import AlphaEarthDataIngestion
from src.data_ingestion.nasa_ingestion import NASADataIngestion
from src.data_ingestion.sentinel_ingestion import SentinelDataIngestion
from src.data_ingestion.noaa_ingestion import NOAADataIngestion
from src.data_ingestion.osm_ingestion import OSMDataIngestion
from src.databricks_integration.delta_lake import delta_lake_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class DataIngestionRequest(BaseModel):
    """Request model for data ingestion"""
    data_source: str = Field(
        ...,
        description="Data source to ingest from",
        enum=["alphaearth", "nasa", "sentinel", "noaa", "osm", "all"]
    )
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates for data extraction",
        example=[[-74.0059, 40.7128], [-74.0059, 40.7589],
                 [-73.9352, 40.7589], [-73.9352, 40.7128]]
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for data extraction (start_date, end_date)"
    )
    data_types: Optional[List[str]] = Field(
        default=None,
        description="Specific data types to extract"
    )


class DataIngestionResponse(BaseModel):
    """Response model for data ingestion"""
    ingestion_id: str
    status: str
    data_source: str
    records_ingested: int
    file_paths: List[str]
    metadata: Dict[str, Any]


@router.post("/ingest", response_model=DataIngestionResponse)
async def ingest_data(
    request: DataIngestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Ingest data from external sources (NASA, Sentinel, NOAA, OSM)
    """
    try:
        ingestion_id = f"ingestion_{hash(str(request.coordinates))}"

        if request.data_source == "alphaearth":
            ingester = AlphaEarthDataIngestion()
            result = await ingester.ingest_data(
                coordinates=request.coordinates,
                date_range=request.date_range,
                data_types=request.data_types
            )

            # Process and store data in Delta Lake
            if result.get("alphaearth_data"):
                for data_type, data in result["alphaearth_data"].items():
                    try:
                        if data_type == "satellite":
                            processed_data = await delta_lake_manager.process_satellite_data(
                                data, request.coordinates
                            )
                        elif data_type == "soil":
                            processed_data = await delta_lake_manager.process_soil_data(
                                data, request.coordinates
                            )
                        elif data_type == "climate":
                            processed_data = await delta_lake_manager.process_climate_data(
                                data, request.coordinates
                            )
                        else:
                            # Store raw data for other types
                            await delta_lake_manager.store_alphaearth_data(
                                data_type, data, request.coordinates
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to process {data_type} data: {str(e)}")
                        continue

        elif request.data_source == "nasa":
            ingester = NASADataIngestion()
            result = await ingester.ingest_data(
                coordinates=request.coordinates,
                date_range=request.date_range,
                data_types=request.data_types
            )
        elif request.data_source == "sentinel":
            ingester = SentinelDataIngestion()
            result = await ingester.ingest_data(
                coordinates=request.coordinates,
                date_range=request.date_range,
                data_types=request.data_types
            )
        elif request.data_source == "noaa":
            ingester = NOAADataIngestion()
            result = await ingester.ingest_data(
                coordinates=request.coordinates,
                date_range=request.date_range,
                data_types=request.data_types
            )
        elif request.data_source == "osm":
            ingester = OSMDataIngestion()
            result = await ingester.ingest_data(
                coordinates=request.coordinates,
                date_range=request.date_range,
                data_types=request.data_types
            )
        elif request.data_source == "all":
            # Ingest from all sources
            result = await ingest_from_all_sources(
                coordinates=request.coordinates,
                date_range=request.date_range,
                data_types=request.data_types
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid data source specified"
            )

        response = DataIngestionResponse(
            ingestion_id=ingestion_id,
            status="completed",
            data_source=request.data_source,
            records_ingested=result.get("records_ingested", 0),
            file_paths=result.get("file_paths", []),
            metadata={
                "coordinates": request.coordinates,
                "date_range": request.date_range,
                "data_types": request.data_types,
                "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
            }
        )

        logger.info(f"Data ingestion completed for {request.data_source}")
        return response

    except Exception as e:
        logger.error(f"Error in data ingestion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data ingestion failed: {str(e)}"
        )


async def ingest_from_all_sources(
    coordinates: List[List[float]],
    date_range: Optional[Dict[str, str]] = None,
    data_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Ingest data from all available sources"""
    results = {
        "records_ingested": 0,
        "file_paths": [],
        "sources": {}
    }

    sources = ["alphaearth", "nasa", "sentinel", "noaa", "osm"]

    for source in sources:
        try:
            if source == "alphaearth":
                ingester = AlphaEarthDataIngestion()
            elif source == "nasa":
                ingester = NASADataIngestion()
            elif source == "sentinel":
                ingester = SentinelDataIngestion()
            elif source == "noaa":
                ingester = NOAADataIngestion()
            elif source == "osm":
                ingester = OSMDataIngestion()

            result = await ingester.ingest_data(
                coordinates=coordinates,
                date_range=date_range,
                data_types=data_types
            )

            results["sources"][source] = result
            results["records_ingested"] += result.get("records_ingested", 0)
            results["file_paths"].extend(result.get("file_paths", []))

        except Exception as e:
            logger.error(f"Failed to ingest from {source}: {str(e)}")
            results["sources"][source] = {"error": str(e)}

    return results


@router.get("/sources")
async def get_available_data_sources():
    """
    Get list of available data sources and their capabilities
    """
    return {
        "sources": [
            {
                "name": "alphaearth",
                "description": "AlphaEarth - Comprehensive environmental data platform with satellite, soil, water, and climate data",
                "data_types": ["satellite", "soil", "water", "climate", "vegetation", "elevation", "land_cover", "urban_heat", "air_quality", "carbon_sequestration"],
                "update_frequency": "real-time",
                "coverage": "global",
                "features": ["High-resolution satellite imagery", "Real-time climate data", "Soil composition analysis", "Water quality monitoring", "Vegetation health indices", "Urban heat island detection", "Air quality measurements", "Carbon sequestration analysis"]
            },
            {
                "name": "nasa",
                "description": "NASA EarthData - Satellite imagery and environmental data",
                "data_types": ["landsat", "modis", "sentinel-2", "temperature", "precipitation"],
                "update_frequency": "daily",
                "coverage": "global"
            },
            {
                "name": "sentinel",
                "description": "Sentinel Hub - European Space Agency satellite data",
                "data_types": ["sentinel-1", "sentinel-2", "sentinel-3", "dem"],
                "update_frequency": "daily",
                "coverage": "global"
            },
            {
                "name": "noaa",
                "description": "NOAA - Weather and climate data",
                "data_types": ["weather", "climate", "precipitation", "temperature"],
                "update_frequency": "hourly",
                "coverage": "global"
            },
            {
                "name": "osm",
                "description": "OpenStreetMap - Open source mapping data",
                "data_types": ["buildings", "roads", "landuse", "waterways"],
                "update_frequency": "continuous",
                "coverage": "global"
            }
        ]
    }


@router.get("/ingestion-status/{ingestion_id}")
async def get_ingestion_status(ingestion_id: str):
    """
    Get status of a data ingestion job
    """
    # TODO: Implement status tracking
    return {
        "ingestion_id": ingestion_id,
        "status": "completed",
        "progress": 100,
        "message": "Data ingestion completed successfully"
    }


@router.delete("/ingestion/{ingestion_id}")
async def delete_ingestion_data(ingestion_id: str):
    """
    Delete ingested data by ingestion ID
    """
    # TODO: Implement data deletion
    return {
        "ingestion_id": ingestion_id,
        "status": "deleted",
        "message": "Data deleted successfully"
    }


@router.get("/data-catalog")
async def get_data_catalog():
    """
    Get catalog of available data in the system
    """
    # TODO: Implement data catalog
    return {
        "catalog": {
            "total_datasets": 0,
            "data_sources": [],
            "last_updated": "2024-01-01T00:00:00Z"
        }
    }
