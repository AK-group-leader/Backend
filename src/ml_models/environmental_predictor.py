"""
Main environmental predictor for comprehensive analysis
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from .heat_island_predictor import HeatIslandPredictor
from .water_absorption_predictor import WaterAbsorptionPredictor
from .air_quality_predictor import AirQualityPredictor
from src.databricks_integration.delta_lake import delta_lake_manager

logger = logging.getLogger(__name__)


class EnvironmentalPredictor:
    """Main environmental predictor for comprehensive analysis"""

    def __init__(self):
        """Initialize environmental predictor"""
        self.heat_island_predictor = HeatIslandPredictor()
        self.water_absorption_predictor = WaterAbsorptionPredictor()
        self.air_quality_predictor = AirQualityPredictor()

    async def comprehensive_analysis(
        self,
        coordinates: List[List[float]],
        time_horizon: int = 10
    ) -> Dict[str, Any]:
        """
        Perform comprehensive environmental analysis using AlphaEarth data

        Args:
            coordinates: Analysis area coordinates
            time_horizon: Time horizon in years

        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info(
                f"Starting comprehensive analysis for area: {coordinates}")

            # Get AlphaEarth data from Delta Lake
            alphaearth_data = await self._get_alphaearth_data(coordinates)

            # Run individual analyses with real data
            heat_island_results = await self.heat_island_predictor.analyze_heat_island_effect(
                coordinates=coordinates,
                time_horizon=time_horizon,
                alphaearth_data=alphaearth_data
            )

            water_absorption_results = await self.water_absorption_predictor.analyze_water_absorption(
                coordinates=coordinates,
                time_horizon=time_horizon,
                alphaearth_data=alphaearth_data
            )

            air_quality_results = await self.air_quality_predictor.analyze_air_quality_impact(
                coordinates=coordinates,
                time_horizon=time_horizon,
                alphaearth_data=alphaearth_data
            )

            # Combine results
            comprehensive_results = {
                "heat_island": heat_island_results,
                "water_absorption": water_absorption_results,
                "air_quality": air_quality_results,
                "overall_risk_score": self._calculate_overall_risk_score(
                    heat_island_results,
                    water_absorption_results,
                    air_quality_results
                ),
                "analysis_metadata": {
                    "coordinates": coordinates,
                    "time_horizon": time_horizon,
                    "analysis_date": datetime.now().isoformat(),
                    "model_versions": {
                        "heat_island": "v1.0",
                        "water_absorption": "v1.0",
                        "air_quality": "v1.0"
                    }
                }
            }

            logger.info("Comprehensive analysis completed successfully")
            return comprehensive_results

        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {str(e)}")
            raise

    async def comprehensive_prediction(
        self,
        input_data: Dict[str, Any],
        horizon: int = 10,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Make comprehensive predictions using all models

        Args:
            input_data: Input data for predictions
            horizon: Prediction horizon in years
            confidence_level: Confidence level for predictions

        Returns:
            Comprehensive prediction results
        """
        try:
            # Make predictions with individual models
            heat_predictions = await self.heat_island_predictor.predict(
                input_data=input_data,
                horizon=horizon,
                confidence_level=confidence_level
            )

            water_predictions = await self.water_absorption_predictor.predict(
                input_data=input_data,
                horizon=horizon,
                confidence_level=confidence_level
            )

            air_predictions = await self.air_quality_predictor.predict(
                input_data=input_data,
                horizon=horizon,
                confidence_level=confidence_level
            )

            # Combine predictions
            comprehensive_predictions = {
                "predictions": {
                    "heat_island": heat_predictions["predictions"],
                    "water_absorption": water_predictions["predictions"],
                    "air_quality": air_predictions["predictions"]
                },
                "confidence_intervals": {
                    "heat_island": heat_predictions["confidence_intervals"],
                    "water_absorption": water_predictions["confidence_intervals"],
                    "air_quality": air_predictions["confidence_intervals"]
                },
                "metadata": {
                    "horizon": horizon,
                    "confidence_level": confidence_level,
                    "prediction_date": datetime.now().isoformat(),
                    "model_versions": {
                        "heat_island": "v1.0",
                        "water_absorption": "v1.0",
                        "air_quality": "v1.0"
                    }
                }
            }

            return comprehensive_predictions

        except Exception as e:
            logger.error(f"Comprehensive prediction failed: {str(e)}")
            raise

    async def analyze_heat_island_effect(
        self,
        coordinates: List[List[float]],
        time_horizon: int = 10
    ) -> Dict[str, Any]:
        """Analyze heat island effect"""
        return await self.heat_island_predictor.analyze_heat_island_effect(
            coordinates=coordinates,
            time_horizon=time_horizon
        )

    async def analyze_water_absorption(
        self,
        coordinates: List[List[float]],
        time_horizon: int = 10
    ) -> Dict[str, Any]:
        """Analyze water absorption"""
        return await self.water_absorption_predictor.analyze_water_absorption(
            coordinates=coordinates,
            time_horizon=time_horizon
        )

    async def analyze_air_quality_impact(
        self,
        coordinates: List[List[float]],
        time_horizon: int = 10
    ) -> Dict[str, Any]:
        """Analyze air quality impact"""
        return await self.air_quality_predictor.analyze_air_quality_impact(
            coordinates=coordinates,
            time_horizon=time_horizon
        )

    async def generate_recommendations(
        self,
        analysis_results: Dict[str, Any],
        analysis_type: str = "comprehensive"
    ) -> List[Dict[str, Any]]:
        """
        Generate sustainability recommendations based on analysis results

        Args:
            analysis_results: Results from environmental analysis
            analysis_type: Type of analysis performed

        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            if analysis_type in ["heat_island", "comprehensive"]:
                heat_recommendations = await self._generate_heat_island_recommendations(
                    analysis_results.get("heat_island", {})
                )
                recommendations.extend(heat_recommendations)

            if analysis_type in ["water_absorption", "comprehensive"]:
                water_recommendations = await self._generate_water_absorption_recommendations(
                    analysis_results.get("water_absorption", {})
                )
                recommendations.extend(water_recommendations)

            if analysis_type in ["air_quality", "comprehensive"]:
                air_recommendations = await self._generate_air_quality_recommendations(
                    analysis_results.get("air_quality", {})
                )
                recommendations.extend(air_recommendations)

            # Sort recommendations by priority
            recommendations.sort(key=lambda x: x.get(
                "priority", 0), reverse=True)

            return recommendations

        except Exception as e:
            logger.error(f"Recommendation generation failed: {str(e)}")
            raise

    async def _get_alphaearth_data(self, coordinates: List[List[float]]) -> Dict[str, Any]:
        """
        Get AlphaEarth data from Delta Lake for analysis

        Args:
            coordinates: Analysis area coordinates

        Returns:
            Dictionary containing AlphaEarth data
        """
        try:
            alphaearth_data = {}

            # Get different types of processed data
            data_types = ["satellite_processed",
                          "soil_processed", "climate_processed"]

            for data_type in data_types:
                try:
                    data = await delta_lake_manager.get_processed_data(
                        data_type=data_type,
                        coordinates=coordinates
                    )
                    if data:
                        # Get most recent record
                        alphaearth_data[data_type] = data[0]
                except Exception as e:
                    logger.warning(f"Could not retrieve {data_type}: {str(e)}")
                    continue

            return alphaearth_data

        except Exception as e:
            logger.error(f"Failed to get AlphaEarth data: {str(e)}")
            return {}

    def _calculate_overall_risk_score(
        self,
        heat_island_results: Dict[str, Any],
        water_absorption_results: Dict[str, Any],
        air_quality_results: Dict[str, Any]
    ) -> float:
        """Calculate overall environmental risk score"""
        try:
            # Extract risk scores from individual analyses
            heat_risk = heat_island_results.get("heat_risk_score", 0.5)
            water_risk = water_absorption_results.get("flood_risk_score", 0.5)
            air_risk = air_quality_results.get("air_quality_risk_score", 0.5)

            # Weighted average (can be adjusted based on priorities)
            weights = {"heat": 0.4, "water": 0.3, "air": 0.3}

            overall_risk = (
                weights["heat"] * heat_risk +
                weights["water"] * water_risk +
                weights["air"] * air_risk
            )

            return round(overall_risk, 3)

        except Exception as e:
            logger.error(f"Risk score calculation failed: {str(e)}")
            return 0.5  # Default moderate risk

    async def _generate_heat_island_recommendations(
        self,
        heat_island_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate heat island mitigation recommendations"""
        recommendations = []

        heat_risk = heat_island_results.get("heat_risk_score", 0.5)

        if heat_risk > 0.7:
            recommendations.extend([
                {
                    "type": "green_infrastructure",
                    "title": "Implement Green Roofs",
                    "description": "Install green roofs on buildings to reduce heat absorption",
                    "impact": "High",
                    "cost": "Medium",
                    "priority": 1,
                    "implementation_time": "6-12 months"
                },
                {
                    "type": "vegetation",
                    "title": "Increase Tree Canopy",
                    "description": "Plant trees to provide shade and cooling",
                    "impact": "High",
                    "cost": "Low",
                    "priority": 1,
                    "implementation_time": "1-3 years"
                }
            ])
        elif heat_risk > 0.4:
            recommendations.append({
                "type": "materials",
                "title": "Use Reflective Materials",
                "description": "Replace dark surfaces with reflective materials",
                "impact": "Medium",
                "cost": "Medium",
                "priority": 2,
                "implementation_time": "3-6 months"
            })

        return recommendations

    async def _generate_water_absorption_recommendations(
        self,
        water_absorption_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate water absorption improvement recommendations"""
        recommendations = []

        flood_risk = water_absorption_results.get("flood_risk_score", 0.5)

        if flood_risk > 0.7:
            recommendations.extend([
                {
                    "type": "infrastructure",
                    "title": "Install Permeable Pavement",
                    "description": "Replace impervious surfaces with permeable materials",
                    "impact": "High",
                    "cost": "High",
                    "priority": 1,
                    "implementation_time": "6-18 months"
                },
                {
                    "type": "infrastructure",
                    "title": "Create Rain Gardens",
                    "description": "Install rain gardens to capture and filter stormwater",
                    "impact": "High",
                    "cost": "Medium",
                    "priority": 1,
                    "implementation_time": "3-6 months"
                }
            ])
        elif flood_risk > 0.4:
            recommendations.append({
                "type": "infrastructure",
                "title": "Improve Drainage Systems",
                "description": "Upgrade existing drainage infrastructure",
                "impact": "Medium",
                "cost": "Medium",
                "priority": 2,
                "implementation_time": "6-12 months"
            })

        return recommendations

    async def _generate_air_quality_recommendations(
        self,
        air_quality_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate air quality improvement recommendations"""
        recommendations = []

        air_risk = air_quality_results.get("air_quality_risk_score", 0.5)

        if air_risk > 0.7:
            recommendations.extend([
                {
                    "type": "transportation",
                    "title": "Promote Electric Vehicles",
                    "description": "Install EV charging stations and promote electric vehicle use",
                    "impact": "High",
                    "cost": "High",
                    "priority": 1,
                    "implementation_time": "12-24 months"
                },
                {
                    "type": "vegetation",
                    "title": "Plant Air-Purifying Vegetation",
                    "description": "Plant trees and vegetation that filter air pollutants",
                    "impact": "Medium",
                    "cost": "Low",
                    "priority": 1,
                    "implementation_time": "1-3 years"
                }
            ])
        elif air_risk > 0.4:
            recommendations.append({
                "type": "transportation",
                "title": "Improve Public Transit",
                "description": "Enhance public transportation to reduce vehicle emissions",
                "impact": "Medium",
                "cost": "High",
                "priority": 2,
                "implementation_time": "12-36 months"
            })

        return recommendations
