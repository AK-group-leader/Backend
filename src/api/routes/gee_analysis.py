"""
Google Earth Engine Analysis API routes for Urban Heat Island Mapping,
Green Space Optimization, and Sustainable Building Zones
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from src.services.gee_service import GoogleEarthEngineService
from src.utils.validators import validate_coordinates, validate_area_bounds

logger = logging.getLogger(__name__)
router = APIRouter()


class GEEAnalysisRequest(BaseModel):
    """Request model for Google Earth Engine analysis"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates for analysis area",
        example=[[-77.12, 38.80], [-77.12, 39.00], [-76.90, 39.00], [-76.90, 38.80]]
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for analysis (YYYY-MM-DD format)",
        example={"start_date": "2024-07-01", "end_date": "2024-07-31"}
    )
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis to perform",
        enum=["urban_heat_island", "green_space", "sustainable_zones", "comprehensive"]
    )


class UrbanHeatIslandRequest(BaseModel):
    """Request model for Urban Heat Island analysis"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates for analysis area"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for analysis"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include cooling recommendations"
    )


class GreenSpaceOptimizationRequest(BaseModel):
    """Request model for Green Space Optimization analysis"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates for analysis area"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for analysis"
    )
    population_density_threshold: Optional[float] = Field(
        default=5000.0,
        description="Population density threshold for high-density recommendations"
    )


class SustainableBuildingZonesRequest(BaseModel):
    """Request model for Sustainable Building Zones analysis"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Bounding box coordinates for analysis area"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for analysis"
    )
    include_risk_assessment: bool = Field(
        default=True,
        description="Include flood and erosion risk assessment"
    )


@router.post("/urban-heat-island")
async def analyze_urban_heat_island(
    request: UrbanHeatIslandRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze Urban Heat Island effects using Landsat surface temperature data
    
    This endpoint detects hotspots where planting trees or adding reflective roofs 
    can reduce warming effects.
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

        # Initialize GEE service
        gee_service = GoogleEarthEngineService()
        
        # Perform analysis
        analysis_results = gee_service.get_urban_heat_island_data(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        # Generate cooling recommendations if requested
        recommendations = []
        if request.include_recommendations:
            uhi_intensity = analysis_results.get("uhi_intensity", 0)
            vegetation_percentage = analysis_results.get("vegetation_index", {}).get("mean_ndvi", 0)
            
            if uhi_intensity > 3:
                recommendations.append({
                    "type": "high_uhi_mitigation",
                    "priority": "high",
                    "title": "Reduce Urban Heat Island Effect",
                    "description": f"High UHI intensity detected ({uhi_intensity}°C). Implement cooling strategies.",
                    "strategies": [
                        "Plant more trees in urban areas",
                        "Install reflective/white roofs",
                        "Create green corridors",
                        "Increase water features"
                    ],
                    "estimated_cooling_effect": f"{uhi_intensity * 0.7:.1f}°C reduction possible"
                })
            
            if vegetation_percentage < 0.3:
                recommendations.append({
                    "type": "increase_vegetation",
                    "priority": "medium",
                    "title": "Increase Vegetation Cover",
                    "description": "Low vegetation index detected. Increase green infrastructure.",
                    "strategies": [
                        "Plant native trees and shrubs",
                        "Create rooftop gardens",
                        "Install vertical green walls",
                        "Develop urban parks"
                    ],
                    "estimated_cooling_effect": "2-4°C reduction in shaded areas"
                })

        return {
            "analysis_id": f"uhi_{hash(str(request.coordinates))}",
            "analysis_type": "urban_heat_island",
            "coordinates": request.coordinates,
            "results": analysis_results,
            "recommendations": recommendations,
            "export_info": {
                "task_id": analysis_results.get("export_task_id"),
                "description": "Surface temperature map exported to Google Drive",
                "folder": "GEE_Urban_Analysis"
            },
            "metadata": {
                "data_sources": ["Landsat-9"],
                "resolution": "30m",
                "analysis_completed_at": analysis_results.get("metadata", {}).get("date_range", "unknown")
            }
        }

    except Exception as e:
        logger.error(f"Urban Heat Island analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Urban Heat Island analysis failed: {str(e)}"
        )


@router.post("/green-space-optimization")
async def analyze_green_space_optimization(
    request: GreenSpaceOptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze green space distribution and identify areas lacking vegetation 
    vs high population density for optimization opportunities.
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

        # Initialize GEE service
        gee_service = GoogleEarthEngineService()
        
        # Perform analysis
        analysis_results = gee_service.get_green_space_analysis(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        # Enhance recommendations based on population density
        enhanced_recommendations = analysis_results.get("optimization_recommendations", [])
        green_space_assessment = analysis_results.get("green_space_assessment", {})
        
        population_density = green_space_assessment.get("population_density", 0)
        if population_density > request.population_density_threshold:
            enhanced_recommendations.append({
                "type": "high_density_optimization",
                "priority": "high",
                "title": "High-Density Green Space Strategy",
                "description": f"High population density area ({population_density:.0f} people/km²) needs optimized green space distribution.",
                "strategies": [
                    "Create pocket parks in dense areas",
                    "Install vertical gardens on buildings",
                    "Develop green roofs and walls",
                    "Plant street trees with adequate spacing",
                    "Create community gardens"
                ],
                "estimated_impact": "Improved air quality, reduced heat stress, enhanced well-being"
            })

        return {
            "analysis_id": f"green_space_{hash(str(request.coordinates))}",
            "analysis_type": "green_space_optimization",
            "coordinates": request.coordinates,
            "results": analysis_results,
            "enhanced_recommendations": enhanced_recommendations,
            "export_info": {
                "task_id": analysis_results.get("export_task_id"),
                "description": "Vegetation NDVI map exported to Google Drive",
                "folder": "GEE_Urban_Analysis"
            },
            "metadata": {
                "data_sources": ["Landsat-9", "WorldPop"],
                "resolution": "30m",
                "population_density_threshold": request.population_density_threshold
            }
        }

    except Exception as e:
        logger.error(f"Green space optimization analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Green space optimization analysis failed: {str(e)}"
        )


@router.post("/sustainable-building-zones")
async def analyze_sustainable_building_zones(
    request: SustainableBuildingZonesRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze sustainable building zones by combining soil, water, and environmental data 
    to plan where construction won't worsen flooding or erosion.
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

        # Initialize GEE service
        gee_service = GoogleEarthEngineService()
        
        # Perform analysis
        analysis_results = gee_service.get_sustainable_building_zones(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        # Enhance recommendations based on risk assessment
        enhanced_recommendations = analysis_results.get("recommendations", [])
        suitability_assessment = analysis_results.get("suitability_assessment", {})
        
        if request.include_risk_assessment:
            flood_risk = suitability_assessment.get("flood_risk_percentage", 0)
            erosion_risk = suitability_assessment.get("erosion_risk_percentage", 0)
            
            if flood_risk > 15:
                enhanced_recommendations.append({
                    "type": "flood_mitigation_detailed",
                    "priority": "high",
                    "title": "Flood Risk Mitigation",
                    "description": f"High flood risk detected ({flood_risk:.1f}% of area). Implement comprehensive flood management.",
                    "strategies": [
                        "Elevate building foundations",
                        "Install stormwater management systems",
                        "Create retention ponds",
                        "Use permeable paving materials",
                        "Implement green infrastructure for water absorption"
                    ],
                    "estimated_impact": "Reduced flood damage, improved drainage"
                })
            
            if erosion_risk > 10:
                enhanced_recommendations.append({
                    "type": "erosion_control_detailed",
                    "priority": "medium",
                    "title": "Erosion Control Measures",
                    "description": f"Erosion risk detected ({erosion_risk:.1f}% of area). Implement soil stabilization.",
                    "strategies": [
                        "Plant deep-rooted vegetation",
                        "Install erosion control blankets",
                        "Create terraces on slopes",
                        "Use retaining walls",
                        "Implement proper drainage systems"
                    ],
                    "estimated_impact": "Reduced soil erosion, improved site stability"
                })

        return {
            "analysis_id": f"sustainable_zones_{hash(str(request.coordinates))}",
            "analysis_type": "sustainable_building_zones",
            "coordinates": request.coordinates,
            "results": analysis_results,
            "enhanced_recommendations": enhanced_recommendations,
            "export_info": {
                "task_id": analysis_results.get("export_task_id"),
                "description": "Building suitability map exported to Google Drive",
                "folder": "GEE_Urban_Analysis"
            },
            "metadata": {
                "data_sources": ["Landsat-9", "Sentinel-5P", "SRTM"],
                "resolution": "30m",
                "risk_assessment_included": request.include_risk_assessment
            }
        }

    except Exception as e:
        logger.error(f"Sustainable building zones analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Sustainable building zones analysis failed: {str(e)}"
        )


@router.post("/comprehensive-analysis")
async def get_comprehensive_analysis(
    request: GEEAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Get comprehensive urban analysis combining Urban Heat Island, 
    Green Space Optimization, and Sustainable Building Zones analysis
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

        # Initialize GEE service
        gee_service = GoogleEarthEngineService()
        
        # Perform comprehensive analysis
        analysis_results = gee_service.get_comprehensive_analysis(
            coordinates=request.coordinates,
            date_range=request.date_range
        )

        # Generate integrated recommendations
        integrated_recommendations = []
        
        # Extract key metrics
        uhi_intensity = analysis_results["urban_heat_island"].get("uhi_intensity", 0)
        vegetation_percentage = analysis_results["green_space_optimization"]["vegetation_analysis"].get("vegetation_percentage", 0)
        suitability_percentage = analysis_results["sustainable_building_zones"]["suitability_assessment"].get("suitable_for_construction", 0)
        
        # Integrated recommendations based on all three analyses
        if uhi_intensity > 2 and vegetation_percentage < 25:
            integrated_recommendations.append({
                "type": "integrated_cooling_strategy",
                "priority": "high",
                "title": "Integrated Urban Cooling Strategy",
                "description": "High heat island effect and low vegetation cover detected. Implement comprehensive cooling measures.",
                "strategies": [
                    "Plant trees in areas with high surface temperature",
                    "Create green corridors connecting existing vegetation",
                    "Install reflective surfaces in urban hotspots",
                    "Develop water features for evaporative cooling",
                    "Implement cool roof technologies"
                ],
                "estimated_impact": f"Potential {uhi_intensity * 0.8:.1f}°C temperature reduction"
            })
        
        if suitability_percentage < 40:
            integrated_recommendations.append({
                "type": "site_preparation_strategy",
                "priority": "medium",
                "title": "Site Preparation for Sustainable Development",
                "description": "Limited suitable areas for construction. Implement site preparation strategies.",
                "strategies": [
                    "Improve soil conditions in suitable areas",
                    "Implement slope stabilization measures",
                    "Create drainage systems before construction",
                    "Select optimal building locations based on analysis",
                    "Develop phased construction approach"
                ],
                "estimated_impact": "Improved construction outcomes, reduced environmental impact"
            })

        return {
            "analysis_id": f"comprehensive_{hash(str(request.coordinates))}",
            "analysis_type": "comprehensive_urban_analysis",
            "coordinates": request.coordinates,
            "results": analysis_results,
            "integrated_recommendations": integrated_recommendations,
            "export_info": {
                "total_tasks": analysis_results["summary"]["total_export_tasks"],
                "description": "Multiple analysis maps exported to Google Drive",
                "folder": "GEE_Urban_Analysis",
                "task_ids": [
                    analysis_results["urban_heat_island"].get("export_task_id"),
                    analysis_results["green_space_optimization"].get("export_task_id"),
                    analysis_results["sustainable_building_zones"].get("export_task_id")
                ]
            },
            "summary_metrics": {
                "uhi_intensity": uhi_intensity,
                "vegetation_percentage": vegetation_percentage,
                "construction_suitability": suitability_percentage,
                "overall_urban_health": "good" if uhi_intensity < 3 and vegetation_percentage > 20 else "needs_improvement"
            },
            "metadata": analysis_results["summary"]
        }

    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive analysis failed: {str(e)}"
        )


@router.get("/export-status/{task_id}")
async def check_export_status(task_id: str):
    """
    Check the status of a Google Earth Engine export task
    """
    try:
        gee_service = GoogleEarthEngineService()
        status = gee_service.check_export_status(task_id)
        
        return {
            "task_id": task_id,
            "status": status,
            "message": "Use this endpoint to check if your exported maps are ready for download from Google Drive"
        }

    except Exception as e:
        logger.error(f"Export status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Export status check failed: {str(e)}"
        )


@router.get("/analysis-capabilities")
async def get_analysis_capabilities():
    """
    Get information about available Google Earth Engine analysis capabilities
    """
    return {
        "available_analyses": [
            {
                "name": "Urban Heat Island Mapping",
                "endpoint": "/urban-heat-island",
                "description": "Detect hotspots where planting trees or adding reflective roofs reduces warming",
                "data_sources": ["Landsat-9"],
                "outputs": ["Surface temperature map", "UHI intensity", "Cooling recommendations"]
            },
            {
                "name": "Green Space Optimization",
                "endpoint": "/green-space-optimization",
                "description": "Identify areas lacking vegetation vs high population density",
                "data_sources": ["Landsat-9", "WorldPop"],
                "outputs": ["Vegetation map", "Land cover classification", "Optimization recommendations"]
            },
            {
                "name": "Sustainable Building Zones",
                "endpoint": "/sustainable-building-zones",
                "description": "Combine soil/water data to plan construction zones that won't worsen flooding/erosion",
                "data_sources": ["Landsat-9", "Sentinel-5P", "SRTM"],
                "outputs": ["Suitability map", "Risk assessment", "Construction recommendations"]
            },
            {
                "name": "Comprehensive Analysis",
                "endpoint": "/comprehensive-analysis",
                "description": "Complete urban analysis combining all three analyses",
                "data_sources": ["Landsat-9", "Sentinel-5P", "SRTM", "WorldPop"],
                "outputs": ["All maps", "Integrated recommendations", "Summary metrics"]
            }
        ],
        "data_requirements": {
            "coordinates": "Bounding box coordinates (4 points)",
            "date_range": "Optional date range (defaults to last 30 days)",
            "area_limit": "Maximum 100 km² analysis area"
        },
        "export_information": {
            "destination": "Google Drive folder 'GEE_Urban_Analysis'",
            "formats": ["GeoTIFF"],
            "resolution": "30m",
            "coordinate_system": "EPSG:4326 (WGS84)"
        },
        "authentication": {
            "required": "Google Earth Engine service account or user authentication",
            "setup": "Configure GEE_PROJECT, GEE_SERVICE_ACCOUNT, and GEE_KEY_FILE in environment variables"
        }
    }
