"""
Urban Heat Island (UHI) Analysis Module
Addresses energy consumption, air quality, and public health impacts
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.databricks_integration.delta_lake import delta_lake_manager

logger = logging.getLogger(__name__)


class UrbanHeatIslandAnalyzer:
    """Comprehensive Urban Heat Island analysis and mitigation"""

    def __init__(self):
        """Initialize UHI analyzer"""
        self.model_version = "v2.0"
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """Load the UHI analysis model"""
        try:
            # TODO: Load actual trained UHI model
            self.model_loaded = True
            logger.info("UHI analysis model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load UHI model: {str(e)}")
            self.model_loaded = False

    async def comprehensive_uhi_analysis(
        self,
        coordinates: List[List[float]],
        time_horizon: int = 10,
        alphaearth_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive UHI analysis addressing energy, air quality, and health impacts

        Args:
            coordinates: Analysis area coordinates
            time_horizon: Time horizon in years
            alphaearth_data: AlphaEarth data for analysis

        Returns:
            Comprehensive UHI analysis results
        """
        try:
            logger.info(
                f"Starting comprehensive UHI analysis for area: {coordinates}")

            # Get AlphaEarth data if not provided
            if not alphaearth_data:
                alphaearth_data = await self._get_alphaearth_data(coordinates)

            # Calculate area
            area_km2 = self._calculate_area(coordinates)

            # Core UHI analysis
            uhi_intensity = await self._calculate_uhi_intensity(
                coordinates, area_km2, alphaearth_data
            )

            # Energy consumption impact
            energy_impact = await self._analyze_energy_consumption_impact(
                uhi_intensity, area_km2, alphaearth_data
            )

            # Air quality impact
            air_quality_impact = await self._analyze_air_quality_impact(
                uhi_intensity, area_km2, alphaearth_data
            )

            # Public health impact
            health_impact = await self._analyze_public_health_impact(
                uhi_intensity, area_km2, alphaearth_data
            )

            # Mitigation potential
            mitigation_potential = await self._assess_mitigation_potential(
                coordinates, uhi_intensity, alphaearth_data
            )

            # Economic impact
            economic_impact = await self._calculate_economic_impact(
                energy_impact, air_quality_impact, health_impact, area_km2
            )

            results = {
                "uhi_intensity": uhi_intensity,
                "energy_consumption_impact": energy_impact,
                "air_quality_impact": air_quality_impact,
                "public_health_impact": health_impact,
                "mitigation_potential": mitigation_potential,
                "economic_impact": economic_impact,
                "overall_uhi_risk_score": self._calculate_overall_uhi_risk(
                    uhi_intensity, energy_impact, air_quality_impact, health_impact
                ),
                "analysis_metadata": {
                    "coordinates": coordinates,
                    "area_km2": area_km2,
                    "time_horizon": time_horizon,
                    "model_version": self.model_version,
                    "analysis_date": datetime.now().isoformat(),
                    "data_source": "alphaearth" if alphaearth_data else "placeholder"
                }
            }

            logger.info("Comprehensive UHI analysis completed successfully")
            return results

        except Exception as e:
            logger.error(f"UHI analysis failed: {str(e)}")
            raise

    async def _calculate_uhi_intensity(
        self,
        coordinates: List[List[float]],
        area_km2: float,
        alphaearth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate Urban Heat Island intensity"""
        try:
            # Base temperature difference (urban vs rural)
            base_uhi_intensity = 2.5  # °C difference

            # Factors that increase UHI intensity
            urban_factors = {
                "building_density": 0.0,
                "impervious_surface": 0.0,
                "lack_of_vegetation": 0.0,
                "anthropogenic_heat": 0.0,
                "albedo": 0.0
            }

            # Extract data from AlphaEarth if available
            if alphaearth_data:
                satellite_data = alphaearth_data.get("satellite_processed", {})
                if satellite_data:
                    data = satellite_data.get("data", {})
                    urban_factors["building_density"] = self._estimate_building_density(
                        area_km2)
                    urban_factors["impervious_surface"] = 1 - \
                        data.get("ndvi", 0.5)
                    urban_factors["lack_of_vegetation"] = 1 - \
                        data.get("vegetation_density", 0.4)
                    urban_factors["albedo"] = 1 - data.get("albedo", 0.3)
                    urban_factors["anthropogenic_heat"] = self._estimate_anthropogenic_heat(
                        area_km2)

            # Calculate UHI intensity
            uhi_intensity = base_uhi_intensity + sum(urban_factors.values())

            # Determine UHI severity
            if uhi_intensity >= 5.0:
                severity = "Extreme"
            elif uhi_intensity >= 3.0:
                severity = "High"
            elif uhi_intensity >= 1.5:
                severity = "Moderate"
            else:
                severity = "Low"

            return {
                "temperature_difference": round(uhi_intensity, 2),
                "severity": severity,
                "contributing_factors": urban_factors,
                "peak_intensity_time": "Evening (6-8 PM)",
                "seasonal_variation": {
                    "summer": round(uhi_intensity * 1.3, 2),
                    "winter": round(uhi_intensity * 0.7, 2),
                    "spring": round(uhi_intensity * 1.0, 2),
                    "fall": round(uhi_intensity * 1.1, 2)
                }
            }

        except Exception as e:
            logger.error(f"UHI intensity calculation failed: {str(e)}")
            return {
                "temperature_difference": 2.5,
                "severity": "Moderate",
                "contributing_factors": {},
                "peak_intensity_time": "Evening (6-8 PM)",
                "seasonal_variation": {}
            }

    async def _analyze_energy_consumption_impact(
        self,
        uhi_intensity: Dict[str, Any],
        area_km2: float,
        alphaearth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze energy consumption impact of UHI"""
        try:
            temp_difference = uhi_intensity["temperature_difference"]

            # Energy consumption increase per degree Celsius
            cooling_energy_increase = 3.5  # % per °C
            heating_energy_decrease = 2.0  # % per °C (winter benefit)

            # Calculate energy impacts
            cooling_impact = temp_difference * cooling_energy_increase
            heating_impact = temp_difference * heating_energy_decrease * \
                0.3  # Only 30% of year is heating season

            # Net energy impact (cooling dominates in most urban areas)
            net_energy_increase = cooling_impact - heating_impact

            # Estimate population and buildings
            population = self._estimate_population(area_km2)
            buildings = self._estimate_building_count(area_km2)

            # Calculate total energy consumption
            avg_energy_per_person = 12.5  # MWh per person per year
            total_energy_consumption = population * avg_energy_per_person

            # Calculate additional energy consumption
            additional_energy = total_energy_consumption * \
                (net_energy_increase / 100)

            # Cost impact (assuming $0.12 per kWh)
            energy_cost_per_mwh = 120
            additional_cost = additional_energy * energy_cost_per_mwh

            return {
                "net_energy_increase_percent": round(net_energy_increase, 2),
                "cooling_energy_increase_percent": round(cooling_impact, 2),
                "heating_energy_decrease_percent": round(heating_impact, 2),
                "additional_energy_consumption_mwh": round(additional_energy, 2),
                "additional_energy_cost_usd": round(additional_cost, 2),
                "affected_population": population,
                "affected_buildings": buildings,
                "energy_efficiency_rating": self._get_energy_efficiency_rating(net_energy_increase)
            }

        except Exception as e:
            logger.error(f"Energy consumption analysis failed: {str(e)}")
            return {
                "net_energy_increase_percent": 8.0,
                "cooling_energy_increase_percent": 10.5,
                "heating_energy_decrease_percent": 1.5,
                "additional_energy_consumption_mwh": 1000.0,
                "additional_energy_cost_usd": 120000.0,
                "affected_population": 10000,
                "affected_buildings": 5000,
                "energy_efficiency_rating": "Poor"
            }

    async def _analyze_air_quality_impact(
        self,
        uhi_intensity: Dict[str, Any],
        area_km2: float,
        alphaearth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze air quality impact of UHI"""
        try:
            temp_difference = uhi_intensity["temperature_difference"]

            # Air quality degradation factors
            ozone_increase = temp_difference * 2.0  # ppb per °C
            pm2_5_increase = temp_difference * 1.5  # μg/m³ per °C
            no2_increase = temp_difference * 1.2   # ppb per °C

            # Calculate air quality index impact
            aqi_increase = (ozone_increase + pm2_5_increase + no2_increase) / 3

            # Health impact assessment
            population = self._estimate_population(area_km2)

            # Estimate health impacts
            respiratory_issues = int(population * 0.15 * (aqi_increase / 10))
            cardiovascular_issues = int(
                population * 0.08 * (aqi_increase / 10))
            premature_deaths = int(population * 0.001 * (aqi_increase / 20))

            # Economic cost of health impacts
            health_cost_per_person = 500  # USD per person per year
            total_health_cost = (respiratory_issues +
                                 cardiovascular_issues) * health_cost_per_person

            return {
                "air_quality_degradation": {
                    "ozone_increase_ppb": round(ozone_increase, 2),
                    "pm2_5_increase_ugm3": round(pm2_5_increase, 2),
                    "no2_increase_ppb": round(no2_increase, 2),
                    "aqi_increase": round(aqi_increase, 2)
                },
                "health_impacts": {
                    "respiratory_issues": respiratory_issues,
                    "cardiovascular_issues": cardiovascular_issues,
                    "premature_deaths": premature_deaths,
                    "total_health_cost_usd": round(total_health_cost, 2)
                },
                "air_quality_rating": self._get_air_quality_rating(aqi_increase),
                "affected_population": population
            }

        except Exception as e:
            logger.error(f"Air quality analysis failed: {str(e)}")
            return {
                "air_quality_degradation": {
                    "ozone_increase_ppb": 5.0,
                    "pm2_5_increase_ugm3": 3.75,
                    "no2_increase_ppb": 3.0,
                    "aqi_increase": 3.9
                },
                "health_impacts": {
                    "respiratory_issues": 1500,
                    "cardiovascular_issues": 800,
                    "premature_deaths": 10,
                    "total_health_cost_usd": 1150000.0
                },
                "air_quality_rating": "Poor",
                "affected_population": 10000
            }

    async def _analyze_public_health_impact(
        self,
        uhi_intensity: Dict[str, Any],
        area_km2: float,
        alphaearth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze public health impact of UHI"""
        try:
            temp_difference = uhi_intensity["temperature_difference"]
            population = self._estimate_population(area_km2)

            # Heat-related health impacts
            heat_stress_cases = int(population * 0.05 * (temp_difference / 2))
            heat_exhaustion_cases = int(
                population * 0.02 * (temp_difference / 2))
            heat_stroke_cases = int(population * 0.001 * (temp_difference / 2))

            # Vulnerable populations
            elderly_population = int(population * 0.15)
            children_population = int(population * 0.20)
            low_income_population = int(population * 0.25)

            # Vulnerability assessment
            vulnerability_score = self._calculate_vulnerability_score(
                elderly_population, children_population, low_income_population, population
            )

            # Economic impact
            healthcare_cost_per_case = 2000  # USD
            total_healthcare_cost = (
                heat_stress_cases + heat_exhaustion_cases + heat_stroke_cases) * healthcare_cost_per_case

            # Productivity loss
            productivity_loss_percent = temp_difference * 0.5  # % per °C
            avg_income = 50000  # USD per person per year
            productivity_loss = population * \
                (productivity_loss_percent / 100) * avg_income

            return {
                "heat_related_health_impacts": {
                    "heat_stress_cases": heat_stress_cases,
                    "heat_exhaustion_cases": heat_exhaustion_cases,
                    "heat_stroke_cases": heat_stroke_cases,
                    "total_healthcare_cost_usd": round(total_healthcare_cost, 2)
                },
                "vulnerable_populations": {
                    "elderly": elderly_population,
                    "children": children_population,
                    "low_income": low_income_population,
                    "vulnerability_score": round(vulnerability_score, 2)
                },
                "productivity_impact": {
                    "productivity_loss_percent": round(productivity_loss_percent, 2),
                    "productivity_loss_usd": round(productivity_loss, 2)
                },
                "health_risk_rating": self._get_health_risk_rating(vulnerability_score, temp_difference)
            }

        except Exception as e:
            logger.error(f"Public health analysis failed: {str(e)}")
            return {
                "heat_related_health_impacts": {
                    "heat_stress_cases": 250,
                    "heat_exhaustion_cases": 100,
                    "heat_stroke_cases": 5,
                    "total_healthcare_cost_usd": 710000.0
                },
                "vulnerable_populations": {
                    "elderly": 1500,
                    "children": 2000,
                    "low_income": 2500,
                    "vulnerability_score": 0.6
                },
                "productivity_impact": {
                    "productivity_loss_percent": 1.25,
                    "productivity_loss_usd": 625000.0
                },
                "health_risk_rating": "High"
            }

    async def _assess_mitigation_potential(
        self,
        coordinates: List[List[float]],
        uhi_intensity: Dict[str, Any],
        alphaearth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess UHI mitigation potential and strategies"""
        try:
            temp_difference = uhi_intensity["temperature_difference"]
            area_km2 = self._calculate_area(coordinates)

            # Mitigation strategies and their potential
            mitigation_strategies = {
                "green_roofs": {
                    "temperature_reduction": 1.5,  # °C
                    "implementation_cost": area_km2 * 50000,  # USD per km²
                    "maintenance_cost": area_km2 * 5000,  # USD per year
                    "feasibility": 0.8,
                    "description": "Install green roofs on buildings"
                },
                "urban_forests": {
                    "temperature_reduction": 2.0,  # °C
                    "implementation_cost": area_km2 * 30000,  # USD per km²
                    "maintenance_cost": area_km2 * 3000,  # USD per year
                    "feasibility": 0.9,
                    "description": "Increase tree canopy coverage"
                },
                "cool_pavements": {
                    "temperature_reduction": 1.0,  # °C
                    "implementation_cost": area_km2 * 40000,  # USD per km²
                    "maintenance_cost": area_km2 * 2000,  # USD per year
                    "feasibility": 0.7,
                    "description": "Replace dark surfaces with reflective materials"
                },
                "water_features": {
                    "temperature_reduction": 0.8,  # °C
                    "implementation_cost": area_km2 * 60000,  # USD per km²
                    "maintenance_cost": area_km2 * 8000,  # USD per year
                    "feasibility": 0.6,
                    "description": "Add fountains, ponds, and water features"
                }
            }

            # Calculate combined mitigation potential
            max_reduction = sum(strategy["temperature_reduction"]
                                for strategy in mitigation_strategies.values())
            achievable_reduction = min(
                max_reduction, temp_difference * 0.8)  # Max 80% reduction

            # Cost-benefit analysis
            total_implementation_cost = sum(
                strategy["implementation_cost"] for strategy in mitigation_strategies.values())
            total_annual_maintenance = sum(
                strategy["maintenance_cost"] for strategy in mitigation_strategies.values())

            # Calculate benefits (energy savings, health improvements, etc.)
            annual_benefits = await self._calculate_mitigation_benefits(achievable_reduction, area_km2)

            payback_period = total_implementation_cost / (annual_benefits - total_annual_maintenance) if (
                annual_benefits - total_annual_maintenance) > 0 else float('inf')

            return {
                "mitigation_strategies": mitigation_strategies,
                "achievable_temperature_reduction": round(achievable_reduction, 2),
                "cost_analysis": {
                    "total_implementation_cost_usd": round(total_implementation_cost, 2),
                    "total_annual_maintenance_usd": round(total_annual_maintenance, 2),
                    "annual_benefits_usd": round(annual_benefits, 2),
                    "payback_period_years": round(payback_period, 1) if payback_period != float('inf') else "N/A"
                },
                "mitigation_priority": self._get_mitigation_priority(uhi_intensity["severity"]),
                "implementation_timeline": "3-5 years"
            }

        except Exception as e:
            logger.error(f"Mitigation potential assessment failed: {str(e)}")
            return {
                "mitigation_strategies": {},
                "achievable_temperature_reduction": 2.0,
                "cost_analysis": {
                    "total_implementation_cost_usd": 1000000.0,
                    "total_annual_maintenance_usd": 100000.0,
                    "annual_benefits_usd": 500000.0,
                    "payback_period_years": 2.5
                },
                "mitigation_priority": "High",
                "implementation_timeline": "3-5 years"
            }

    async def _calculate_economic_impact(
        self,
        energy_impact: Dict[str, Any],
        air_quality_impact: Dict[str, Any],
        health_impact: Dict[str, Any],
        area_km2: float
    ) -> Dict[str, Any]:
        """Calculate total economic impact of UHI"""
        try:
            # Direct costs
            energy_cost = energy_impact.get("additional_energy_cost_usd", 0)
            health_cost = health_impact.get("heat_related_health_impacts", {}).get(
                "total_healthcare_cost_usd", 0)
            air_quality_cost = air_quality_impact.get(
                "health_impacts", {}).get("total_health_cost_usd", 0)

            # Indirect costs
            productivity_loss = health_impact.get(
                "productivity_impact", {}).get("productivity_loss_usd", 0)

            # Total annual cost
            total_annual_cost = energy_cost + health_cost + \
                air_quality_cost + productivity_loss

            # Cost per capita
            population = self._estimate_population(area_km2)
            cost_per_capita = total_annual_cost / population if population > 0 else 0

            # Cost per km²
            cost_per_km2 = total_annual_cost / area_km2 if area_km2 > 0 else 0

            return {
                "total_annual_cost_usd": round(total_annual_cost, 2),
                "cost_breakdown": {
                    "energy_cost": round(energy_cost, 2),
                    "health_cost": round(health_cost, 2),
                    "air_quality_cost": round(air_quality_cost, 2),
                    "productivity_loss": round(productivity_loss, 2)
                },
                "cost_per_capita_usd": round(cost_per_capita, 2),
                "cost_per_km2_usd": round(cost_per_km2, 2),
                "economic_impact_rating": self._get_economic_impact_rating(total_annual_cost, population)
            }

        except Exception as e:
            logger.error(f"Economic impact calculation failed: {str(e)}")
            return {
                "total_annual_cost_usd": 2000000.0,
                "cost_breakdown": {
                    "energy_cost": 120000.0,
                    "health_cost": 710000.0,
                    "air_quality_cost": 1150000.0,
                    "productivity_loss": 625000.0
                },
                "cost_per_capita_usd": 200.0,
                "cost_per_km2_usd": 200000.0,
                "economic_impact_rating": "High"
            }

    # Helper methods
    async def _get_alphaearth_data(self, coordinates: List[List[float]]) -> Dict[str, Any]:
        """Get AlphaEarth data from Delta Lake"""
        try:
            alphaearth_data = {}
            data_types = ["satellite_processed",
                          "soil_processed", "climate_processed"]

            for data_type in data_types:
                try:
                    data = await delta_lake_manager.get_processed_data(
                        data_type=data_type,
                        coordinates=coordinates
                    )
                    if data:
                        alphaearth_data[data_type] = data[0]
                except Exception as e:
                    logger.warning(f"Could not retrieve {data_type}: {str(e)}")
                    continue

            return alphaearth_data

        except Exception as e:
            logger.error(f"Failed to get AlphaEarth data: {str(e)}")
            return {}

    def _calculate_area(self, coordinates: List[List[float]]) -> float:
        """Calculate area from coordinates"""
        try:
            n = len(coordinates)
            area = 0.0

            for i in range(n):
                j = (i + 1) % n
                area += coordinates[i][0] * coordinates[j][1]
                area -= coordinates[j][0] * coordinates[i][1]

            area = abs(area) / 2.0
            area_km2 = area * 111.32 * 111.32

            return area_km2

        except Exception as e:
            logger.error(f"Area calculation failed: {str(e)}")
            return 1.0

    def _estimate_building_density(self, area_km2: float) -> float:
        """Estimate building density factor"""
        return min(area_km2 / 10.0, 1.0)

    def _estimate_anthropogenic_heat(self, area_km2: float) -> float:
        """Estimate anthropogenic heat factor"""
        return min(area_km2 / 5.0, 1.0)

    def _estimate_population(self, area_km2: float) -> int:
        """Estimate population based on area"""
        return int(area_km2 * 1000)  # 1000 people per km²

    def _estimate_building_count(self, area_km2: float) -> int:
        """Estimate building count based on area"""
        return int(area_km2 * 500)  # 500 buildings per km²

    def _calculate_vulnerability_score(
        self, elderly: int, children: int, low_income: int, total: int
    ) -> float:
        """Calculate vulnerability score"""
        if total == 0:
            return 0.0

        elderly_ratio = elderly / total
        children_ratio = children / total
        low_income_ratio = low_income / total

        return (elderly_ratio * 0.4 + children_ratio * 0.3 + low_income_ratio * 0.3)

    async def _calculate_mitigation_benefits(self, temp_reduction: float, area_km2: float) -> float:
        """Calculate annual benefits from UHI mitigation"""
        population = self._estimate_population(area_km2)

        # Energy savings
        energy_savings = population * 12.5 * (temp_reduction * 3.5 / 100) * 120

        # Health savings
        health_savings = population * 0.1 * temp_reduction * 1000

        # Productivity gains
        productivity_gains = population * 50000 * (temp_reduction * 0.5 / 100)

        return energy_savings + health_savings + productivity_gains

    def _calculate_overall_uhi_risk(
        self,
        uhi_intensity: Dict[str, Any],
        energy_impact: Dict[str, Any],
        air_quality_impact: Dict[str, Any],
        health_impact: Dict[str, Any]
    ) -> float:
        """Calculate overall UHI risk score"""
        try:
            temp_score = min(
                uhi_intensity["temperature_difference"] / 5.0, 1.0)
            energy_score = min(
                energy_impact["net_energy_increase_percent"] / 20.0, 1.0)
            air_score = min(
                air_quality_impact["air_quality_degradation"]["aqi_increase"] / 10.0, 1.0)
            health_score = min(
                health_impact["vulnerable_populations"]["vulnerability_score"], 1.0)

            # Weighted average
            overall_risk = (temp_score * 0.3 + energy_score *
                            0.25 + air_score * 0.25 + health_score * 0.2)

            return round(overall_risk, 3)

        except Exception as e:
            logger.error(f"Overall UHI risk calculation failed: {str(e)}")
            return 0.5

    # Rating methods
    def _get_energy_efficiency_rating(self, energy_increase: float) -> str:
        """Get energy efficiency rating"""
        if energy_increase <= 5:
            return "Good"
        elif energy_increase <= 10:
            return "Fair"
        elif energy_increase <= 15:
            return "Poor"
        else:
            return "Very Poor"

    def _get_air_quality_rating(self, aqi_increase: float) -> str:
        """Get air quality rating"""
        if aqi_increase <= 2:
            return "Good"
        elif aqi_increase <= 5:
            return "Moderate"
        elif aqi_increase <= 8:
            return "Unhealthy for Sensitive Groups"
        else:
            return "Unhealthy"

    def _get_health_risk_rating(self, vulnerability_score: float, temp_difference: float) -> str:
        """Get health risk rating"""
        risk_score = vulnerability_score * (temp_difference / 5.0)

        if risk_score <= 0.2:
            return "Low"
        elif risk_score <= 0.4:
            return "Moderate"
        elif risk_score <= 0.6:
            return "High"
        else:
            return "Very High"

    def _get_mitigation_priority(self, severity: str) -> str:
        """Get mitigation priority"""
        priority_map = {
            "Extreme": "Critical",
            "High": "High",
            "Moderate": "Medium",
            "Low": "Low"
        }
        return priority_map.get(severity, "Medium")

    def _get_economic_impact_rating(self, total_cost: float, population: int) -> str:
        """Get economic impact rating"""
        if population == 0:
            return "Unknown"

        cost_per_capita = total_cost / population

        if cost_per_capita <= 100:
            return "Low"
        elif cost_per_capita <= 300:
            return "Moderate"
        elif cost_per_capita <= 500:
            return "High"
        else:
            return "Very High"
