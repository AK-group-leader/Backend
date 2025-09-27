"""
Urban Heat Island (UHI) Analysis API routes
Focuses on energy consumption, air quality, and public health impacts
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from src.ml_models.uhi_analyzer import UrbanHeatIslandAnalyzer
from src.databricks_integration.delta_lake import delta_lake_manager
from src.utils.validators import validate_coordinates, validate_area_bounds

logger = logging.getLogger(__name__)
router = APIRouter()


class UHIAnalysisRequest(BaseModel):
    """Request model for UHI analysis"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Analysis area coordinates",
        example=[[-74.0059, 40.7128], [-74.0059, 40.7589],
                 [-73.9352, 40.7589], [-73.9352, 40.7128]]
    )
    time_horizon: int = Field(
        default=10,
        description="Time horizon for analysis in years",
        ge=1,
        le=50
    )
    include_mitigation: bool = Field(
        default=True,
        description="Include mitigation strategies and recommendations"
    )
    include_economic_impact: bool = Field(
        default=True,
        description="Include economic impact analysis"
    )


class UHIMitigationRequest(BaseModel):
    """Request model for UHI mitigation analysis"""
    coordinates: List[List[float]] = Field(
        ...,
        description="Analysis area coordinates"
    )
    mitigation_strategies: List[str] = Field(
        default=["green_roofs", "urban_forests",
                 "cool_pavements", "water_features"],
        description="Mitigation strategies to analyze"
    )
    budget_constraint: Optional[float] = Field(
        default=None,
        description="Budget constraint in USD"
    )
    priority_focus: str = Field(
        default="comprehensive",
        description="Priority focus area",
        enum=["energy_savings", "health_improvement",
              "air_quality", "comprehensive"]
    )


class UHIComparisonRequest(BaseModel):
    """Request model for UHI scenario comparison"""
    baseline_coordinates: List[List[float]] = Field(
        ...,
        description="Baseline scenario coordinates"
    )
    proposed_coordinates: List[List[float]] = Field(
        ...,
        description="Proposed development scenario coordinates"
    )
    development_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Details about proposed development"
    )


@router.post("/comprehensive-analysis")
async def comprehensive_uhi_analysis(
    request: UHIAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Comprehensive UHI analysis addressing energy consumption, air quality, and public health impacts
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

        # Initialize UHI analyzer
        uhi_analyzer = UrbanHeatIslandAnalyzer()

        # Perform comprehensive analysis
        analysis_results = await uhi_analyzer.comprehensive_uhi_analysis(
            coordinates=request.coordinates,
            time_horizon=request.time_horizon
        )

        # Add analysis metadata
        analysis_results["analysis_metadata"].update({
            "include_mitigation": request.include_mitigation,
            "include_economic_impact": request.include_economic_impact,
            "analysis_type": "comprehensive_uhi"
        })

        return {
            "analysis_id": f"uhi_{hash(str(request.coordinates))}",
            "status": "completed",
            "results": analysis_results,
            "metadata": {
                "coordinates": request.coordinates,
                "time_horizon": request.time_horizon,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

    except Exception as e:
        logger.error(f"UHI analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"UHI analysis failed: {str(e)}"
        )


@router.post("/mitigation-analysis")
async def uhi_mitigation_analysis(
    request: UHIMitigationRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze UHI mitigation strategies and their potential impact
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Initialize UHI analyzer
        uhi_analyzer = UrbanHeatIslandAnalyzer()

        # Get baseline UHI analysis
        baseline_analysis = await uhi_analyzer.comprehensive_uhi_analysis(
            coordinates=request.coordinates
        )

        # Analyze mitigation potential
        mitigation_analysis = baseline_analysis.get("mitigation_potential", {})

        # Filter strategies based on budget constraint
        if request.budget_constraint:
            filtered_strategies = {}
            for strategy, details in mitigation_analysis.get("mitigation_strategies", {}).items():
                if details["implementation_cost"] <= request.budget_constraint:
                    filtered_strategies[strategy] = details

            mitigation_analysis["mitigation_strategies"] = filtered_strategies

        # Calculate priority-based recommendations
        priority_recommendations = await _generate_priority_recommendations(
            mitigation_analysis, request.priority_focus
        )

        return {
            "mitigation_id": f"mitigation_{hash(str(request.coordinates))}",
            "status": "completed",
            "baseline_analysis": baseline_analysis,
            "mitigation_analysis": mitigation_analysis,
            "priority_recommendations": priority_recommendations,
            "metadata": {
                "coordinates": request.coordinates,
                "budget_constraint": request.budget_constraint,
                "priority_focus": request.priority_focus,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

    except Exception as e:
        logger.error(f"UHI mitigation analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"UHI mitigation analysis failed: {str(e)}"
        )


@router.post("/scenario-comparison")
async def uhi_scenario_comparison(
    request: UHIComparisonRequest,
    background_tasks: BackgroundTasks
):
    """
    Compare UHI impacts between baseline and proposed development scenarios
    """
    try:
        # Validate coordinates
        if not validate_coordinates(request.baseline_coordinates) or not validate_coordinates(request.proposed_coordinates):
            raise HTTPException(
                status_code=400,
                detail="Invalid coordinates provided"
            )

        # Initialize UHI analyzer
        uhi_analyzer = UrbanHeatIslandAnalyzer()

        # Analyze baseline scenario
        baseline_analysis = await uhi_analyzer.comprehensive_uhi_analysis(
            coordinates=request.baseline_coordinates
        )

        # Analyze proposed scenario
        proposed_analysis = await uhi_analyzer.comprehensive_uhi_analysis(
            coordinates=request.proposed_coordinates
        )

        # Calculate differences
        comparison_results = await _calculate_uhi_differences(
            baseline_analysis, proposed_analysis
        )

        return {
            "comparison_id": f"comparison_{hash(str(request.baseline_coordinates + request.proposed_coordinates))}",
            "status": "completed",
            "baseline_scenario": baseline_analysis,
            "proposed_scenario": proposed_analysis,
            "comparison_results": comparison_results,
            "metadata": {
                "baseline_coordinates": request.baseline_coordinates,
                "proposed_coordinates": request.proposed_coordinates,
                "development_details": request.development_details,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

    except Exception as e:
        logger.error(f"UHI scenario comparison failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"UHI scenario comparison failed: {str(e)}"
        )


@router.get("/uhi-impacts/{analysis_id}")
async def get_uhi_impacts(analysis_id: str):
    """
    Get detailed UHI impact breakdown by analysis ID
    """
    try:
        # TODO: Implement retrieval from database
        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "message": "UHI impacts retrieved successfully",
            "impacts": {
                "energy_consumption": "High impact on cooling energy demand",
                "air_quality": "Significant degradation in air quality",
                "public_health": "Increased heat-related health risks",
                "economic_cost": "Substantial economic burden on community"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get UHI impacts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get UHI impacts: {str(e)}"
        )


@router.get("/mitigation-strategies")
async def get_uhi_mitigation_strategies():
    """
    Get available UHI mitigation strategies and their effectiveness
    """
    try:
        return {
            "mitigation_strategies": [
                {
                    "name": "green_roofs",
                    "title": "Green Roofs",
                    "description": "Install vegetation on building rooftops to reduce heat absorption",
                    "temperature_reduction": "1.5°C",
                    "cost_per_km2": "$50,000",
                    "effectiveness": "High",
                    "implementation_time": "6-12 months",
                    "benefits": [
                        "Reduces building cooling costs",
                        "Improves air quality",
                        "Provides habitat for wildlife",
                        "Reduces stormwater runoff"
                    ]
                },
                {
                    "name": "urban_forests",
                    "title": "Urban Forests",
                    "description": "Increase tree canopy coverage throughout the urban area",
                    "temperature_reduction": "2.0°C",
                    "cost_per_km2": "$30,000",
                    "effectiveness": "Very High",
                    "implementation_time": "1-3 years",
                    "benefits": [
                        "Provides shade and cooling",
                        "Improves air quality",
                        "Reduces noise pollution",
                        "Enhances property values"
                    ]
                },
                {
                    "name": "cool_pavements",
                    "title": "Cool Pavements",
                    "description": "Replace dark surfaces with reflective materials",
                    "temperature_reduction": "1.0°C",
                    "cost_per_km2": "$40,000",
                    "effectiveness": "Medium",
                    "implementation_time": "3-6 months",
                    "benefits": [
                        "Reduces surface temperature",
                        "Improves pedestrian comfort",
                        "Reduces maintenance costs",
                        "Enhances safety"
                    ]
                },
                {
                    "name": "water_features",
                    "title": "Water Features",
                    "description": "Add fountains, ponds, and water features for evaporative cooling",
                    "temperature_reduction": "0.8°C",
                    "cost_per_km2": "$60,000",
                    "effectiveness": "Medium",
                    "implementation_time": "6-18 months",
                    "benefits": [
                        "Provides evaporative cooling",
                        "Enhances aesthetic appeal",
                        "Supports biodiversity",
                        "Creates recreational spaces"
                    ]
                }
            ],
            "implementation_guidelines": {
                "planning_phase": "3-6 months",
                "design_phase": "6-12 months",
                "implementation_phase": "1-3 years",
                "monitoring_phase": "Ongoing"
            },
            "success_factors": [
                "Community engagement and support",
                "Adequate funding and resources",
                "Professional design and implementation",
                "Regular maintenance and monitoring",
                "Integration with existing infrastructure"
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get mitigation strategies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get mitigation strategies: {str(e)}"
        )


# Helper functions
async def _generate_priority_recommendations(
    mitigation_analysis: Dict[str, Any],
    priority_focus: str
) -> List[Dict[str, Any]]:
    """Generate priority-based recommendations"""
    try:
        recommendations = []
        strategies = mitigation_analysis.get("mitigation_strategies", {})

        # Sort strategies by effectiveness for the priority focus
        if priority_focus == "energy_savings":
            # Prioritize strategies that reduce cooling energy demand
            priority_order = ["green_roofs", "urban_forests",
                              "cool_pavements", "water_features"]
        elif priority_focus == "health_improvement":
            # Prioritize strategies that improve air quality and reduce heat stress
            priority_order = ["urban_forests", "green_roofs",
                              "water_features", "cool_pavements"]
        elif priority_focus == "air_quality":
            # Prioritize strategies that improve air quality
            priority_order = ["urban_forests", "green_roofs",
                              "water_features", "cool_pavements"]
        else:  # comprehensive
            # Prioritize by overall effectiveness
            priority_order = ["urban_forests", "green_roofs",
                              "cool_pavements", "water_features"]

        for strategy_name in priority_order:
            if strategy_name in strategies:
                strategy = strategies[strategy_name]
                recommendations.append({
                    "strategy": strategy_name,
                    "title": strategy.get("description", ""),
                    "temperature_reduction": strategy.get("temperature_reduction", 0),
                    "implementation_cost": strategy.get("implementation_cost", 0),
                    "feasibility": strategy.get("feasibility", 0),
                    "priority": len(recommendations) + 1,
                    "rationale": f"Recommended for {priority_focus} focus based on effectiveness and feasibility"
                })

        return recommendations

    except Exception as e:
        logger.error(f"Priority recommendations generation failed: {str(e)}")
        return []


async def _calculate_uhi_differences(
    baseline_analysis: Dict[str, Any],
    proposed_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate differences between baseline and proposed scenarios"""
    try:
        differences = {}

        # Temperature difference
        baseline_temp = baseline_analysis.get(
            "uhi_intensity", {}).get("temperature_difference", 0)
        proposed_temp = proposed_analysis.get(
            "uhi_intensity", {}).get("temperature_difference", 0)
        temp_change = proposed_temp - baseline_temp

        # Energy impact difference
        baseline_energy = baseline_analysis.get(
            "energy_consumption_impact", {}).get("additional_energy_cost_usd", 0)
        proposed_energy = proposed_analysis.get(
            "energy_consumption_impact", {}).get("additional_energy_cost_usd", 0)
        energy_change = proposed_energy - baseline_energy

        # Health impact difference
        baseline_health = baseline_analysis.get("public_health_impact", {}).get(
            "heat_related_health_impacts", {}).get("total_healthcare_cost_usd", 0)
        proposed_health = proposed_analysis.get("public_health_impact", {}).get(
            "heat_related_health_impacts", {}).get("total_healthcare_cost_usd", 0)
        health_change = proposed_health - baseline_health

        # Economic impact difference
        baseline_economic = baseline_analysis.get(
            "economic_impact", {}).get("total_annual_cost_usd", 0)
        proposed_economic = proposed_analysis.get(
            "economic_impact", {}).get("total_annual_cost_usd", 0)
        economic_change = proposed_economic - baseline_economic

        differences = {
            "temperature_change": {
                "baseline": baseline_temp,
                "proposed": proposed_temp,
                "difference": round(temp_change, 2),
                "impact": "Worse" if temp_change > 0 else "Better"
            },
            "energy_impact_change": {
                "baseline": baseline_energy,
                "proposed": proposed_energy,
                "difference": round(energy_change, 2),
                "impact": "Worse" if energy_change > 0 else "Better"
            },
            "health_impact_change": {
                "baseline": baseline_health,
                "proposed": proposed_health,
                "difference": round(health_change, 2),
                "impact": "Worse" if health_change > 0 else "Better"
            },
            "economic_impact_change": {
                "baseline": baseline_economic,
                "proposed": proposed_economic,
                "difference": round(economic_change, 2),
                "impact": "Worse" if economic_change > 0 else "Better"
            },
            "overall_assessment": {
                "net_impact": "Negative" if (temp_change > 0 or energy_change > 0 or health_change > 0) else "Positive",
                "recommendation": "Implement mitigation strategies" if temp_change > 0 else "Development appears sustainable"
            }
        }

        return differences

    except Exception as e:
        logger.error(f"UHI differences calculation failed: {str(e)}")
        return {
            "error": "Failed to calculate differences",
            "message": str(e)
        }
