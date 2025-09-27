"""
Visualization API routes for generating maps and charts
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import io
import json

from src.utils.visualization import MapGenerator, ChartGenerator
from src.utils.geospatial import GeospatialProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


class VisualizationRequest(BaseModel):
    """Request model for visualization generation"""
    visualization_type: str = Field(
        ...,
        description="Type of visualization to generate",
        enum=["heatmap", "before_after", "time_series", "comparison", "3d_model"]
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data to visualize"
    )
    coordinates: List[List[float]] = Field(
        ...,
        description="Geographic coordinates for the visualization area"
    )
    style: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Visualization style options"
    )
    output_format: str = Field(
        default="png",
        description="Output format for the visualization",
        enum=["png", "svg", "html", "geojson"]
    )


class HeatmapRequest(BaseModel):
    """Request model for heatmap generation"""
    data_type: str = Field(
        ...,
        description="Type of data to visualize in heatmap",
        enum=["temperature", "air_quality",
              "water_absorption", "population_density"]
    )
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates"
    )
    resolution: int = Field(
        default=100,
        description="Heatmap resolution (pixels)",
        ge=50,
        le=1000
    )
    color_scheme: str = Field(
        default="viridis",
        description="Color scheme for the heatmap",
        enum=["viridis", "plasma", "inferno", "magma", "coolwarm"]
    )


class BeforeAfterRequest(BaseModel):
    """Request model for before/after comparison visualization"""
    baseline_data: Dict[str, Any] = Field(
        ...,
        description="Baseline scenario data"
    )
    proposed_data: Dict[str, Any] = Field(
        ...,
        description="Proposed scenario data"
    )
    coordinates: List[List[float]] = Field(
        ...,
        description="Geographic coordinates"
    )
    comparison_metrics: List[str] = Field(
        ...,
        description="Metrics to compare"
    )


@router.post("/heatmap")
async def generate_heatmap(request: HeatmapRequest):
    """
    Generate a heatmap visualization
    """
    try:
        map_generator = MapGenerator()

        # Generate heatmap based on data type
        if request.data_type == "temperature":
            heatmap_data = await map_generator.generate_temperature_heatmap(
                coordinates=request.coordinates,
                resolution=request.resolution,
                color_scheme=request.color_scheme
            )
        elif request.data_type == "air_quality":
            heatmap_data = await map_generator.generate_air_quality_heatmap(
                coordinates=request.coordinates,
                resolution=request.resolution,
                color_scheme=request.color_scheme
            )
        elif request.data_type == "water_absorption":
            heatmap_data = await map_generator.generate_water_absorption_heatmap(
                coordinates=request.coordinates,
                resolution=request.resolution,
                color_scheme=request.color_scheme
            )
        elif request.data_type == "population_density":
            heatmap_data = await map_generator.generate_population_heatmap(
                coordinates=request.coordinates,
                resolution=request.resolution,
                color_scheme=request.color_scheme
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid data type for heatmap"
            )

        return {
            "heatmap_id": f"heatmap_{hash(str(request.coordinates))}",
            "data_type": request.data_type,
            "coordinates": request.coordinates,
            "heatmap_data": heatmap_data,
            "metadata": {
                "resolution": request.resolution,
                "color_scheme": request.color_scheme,
                "generated_at": "2024-01-01T00:00:00Z"
            }
        }

    except Exception as e:
        logger.error(f"Error generating heatmap: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Heatmap generation failed: {str(e)}"
        )


@router.post("/before-after")
async def generate_before_after_comparison(request: BeforeAfterRequest):
    """
    Generate before/after comparison visualization
    """
    try:
        map_generator = MapGenerator()

        comparison_viz = await map_generator.generate_before_after_comparison(
            baseline_data=request.baseline_data,
            proposed_data=request.proposed_data,
            coordinates=request.coordinates,
            comparison_metrics=request.comparison_metrics
        )

        return {
            "comparison_id": f"comparison_{hash(str(request.coordinates))}",
            "visualization": comparison_viz,
            "metrics": request.comparison_metrics,
            "coordinates": request.coordinates,
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "baseline_scenario": "current",
                "proposed_scenario": "development"
            }
        }

    except Exception as e:
        logger.error(f"Error generating before/after comparison: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Before/after comparison generation failed: {str(e)}"
        )


@router.post("/time-series")
async def generate_time_series_chart(
    data: Dict[str, Any],
    coordinates: List[List[float]],
    time_range: Dict[str, str],
    metrics: List[str]
):
    """
    Generate time series chart for environmental metrics
    """
    try:
        chart_generator = ChartGenerator()

        time_series_data = await chart_generator.generate_time_series(
            data=data,
            coordinates=coordinates,
            time_range=time_range,
            metrics=metrics
        )

        return {
            "chart_id": f"timeseries_{hash(str(coordinates))}",
            "time_series_data": time_series_data,
            "metrics": metrics,
            "time_range": time_range,
            "coordinates": coordinates,
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "chart_type": "time_series"
            }
        }

    except Exception as e:
        logger.error(f"Error generating time series chart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Time series chart generation failed: {str(e)}"
        )


@router.post("/3d-model")
async def generate_3d_model(
    data: Dict[str, Any],
    coordinates: List[List[float]],
    model_type: str = "terrain"
):
    """
    Generate 3D model visualization
    """
    try:
        map_generator = MapGenerator()

        model_3d = await map_generator.generate_3d_model(
            data=data,
            coordinates=coordinates,
            model_type=model_type
        )

        return {
            "model_id": f"3d_{hash(str(coordinates))}",
            "model_data": model_3d,
            "model_type": model_type,
            "coordinates": coordinates,
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "format": "3d_model"
            }
        }

    except Exception as e:
        logger.error(f"Error generating 3D model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"3D model generation failed: {str(e)}"
        )


@router.get("/map-tiles/{z}/{x}/{y}")
async def get_map_tiles(z: int, x: int, y: int, data_type: str = "satellite"):
    """
    Serve map tiles for web mapping
    """
    try:
        map_generator = MapGenerator()

        tile_data = await map_generator.generate_map_tile(
            z=z, x=x, y=y, data_type=data_type
        )

        return StreamingResponse(
            io.BytesIO(tile_data),
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(f"Error generating map tile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Map tile generation failed: {str(e)}"
        )


@router.post("/export")
async def export_visualization(
    visualization_id: str,
    format: str = "png",
    resolution: str = "high"
):
    """
    Export visualization in various formats
    """
    try:
        # TODO: Implement visualization export
        return {
            "export_id": f"export_{visualization_id}",
            "format": format,
            "resolution": resolution,
            "download_url": f"/api/v1/visualization/download/{visualization_id}",
            "status": "ready"
        }

    except Exception as e:
        logger.error(f"Error exporting visualization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Visualization export failed: {str(e)}"
        )


@router.get("/download/{visualization_id}")
async def download_visualization(visualization_id: str):
    """
    Download exported visualization
    """
    try:
        # TODO: Implement visualization download
        return {
            "visualization_id": visualization_id,
            "message": "Download ready"
        }

    except Exception as e:
        logger.error(f"Error downloading visualization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Visualization download failed: {str(e)}"
        )


@router.get("/visualization-types")
async def get_visualization_types():
    """
    Get available visualization types and their capabilities
    """
    return {
        "visualization_types": [
            {
                "name": "heatmap",
                "description": "Generate heatmap visualizations for environmental data",
                "supported_data": ["temperature", "air_quality", "water_absorption", "population_density"],
                "output_formats": ["png", "svg", "html"]
            },
            {
                "name": "before_after",
                "description": "Compare baseline vs proposed scenarios",
                "supported_data": ["all_environmental_metrics"],
                "output_formats": ["png", "svg", "html"]
            },
            {
                "name": "time_series",
                "description": "Generate time series charts for trends",
                "supported_data": ["all_environmental_metrics"],
                "output_formats": ["png", "svg", "html"]
            },
            {
                "name": "3d_model",
                "description": "Generate 3D terrain and building models",
                "supported_data": ["elevation", "buildings", "vegetation"],
                "output_formats": ["obj", "gltf", "html"]
            }
        ]
    }
