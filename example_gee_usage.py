#!/usr/bin/env python3
"""
Example usage of Google Earth Engine Analysis API
This script demonstrates how to use the GEE analysis endpoints
"""

import requests
import json
import time
from typing import Dict, List, Any


class GEEAnalysisClient:
    """Client for Google Earth Engine Analysis API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1/gee"
    
    def urban_heat_island_analysis(
        self, 
        coordinates: List[List[float]], 
        date_range: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Perform Urban Heat Island analysis"""
        url = f"{self.api_base}/urban-heat-island"
        
        payload = {
            "coordinates": coordinates,
            "include_recommendations": True
        }
        
        if date_range:
            payload["date_range"] = date_range
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def green_space_optimization(
        self, 
        coordinates: List[List[float]], 
        population_threshold: float = 5000.0
    ) -> Dict[str, Any]:
        """Perform Green Space Optimization analysis"""
        url = f"{self.api_base}/green-space-optimization"
        
        payload = {
            "coordinates": coordinates,
            "population_density_threshold": population_threshold
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def sustainable_building_zones(
        self, 
        coordinates: List[List[float]], 
        include_risk_assessment: bool = True
    ) -> Dict[str, Any]:
        """Perform Sustainable Building Zones analysis"""
        url = f"{self.api_base}/sustainable-building-zones"
        
        payload = {
            "coordinates": coordinates,
            "include_risk_assessment": include_risk_assessment
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def comprehensive_analysis(
        self, 
        coordinates: List[List[float]], 
        date_range: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis combining all three"""
        url = f"{self.api_base}/comprehensive-analysis"
        
        payload = {
            "coordinates": coordinates,
            "analysis_type": "comprehensive"
        }
        
        if date_range:
            payload["date_range"] = date_range
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def check_export_status(self, task_id: str) -> Dict[str, Any]:
        """Check the status of an export task"""
        url = f"{self.api_base}/export-status/{task_id}"
        
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about available analysis capabilities"""
        url = f"{self.api_base}/analysis-capabilities"
        
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def example_washington_dc_analysis():
    """Example analysis for Washington, DC area"""
    
    # Washington, DC bounding box coordinates
    dc_coordinates = [
        [-77.12, 38.80],  # Southwest
        [-77.12, 39.00],  # Northwest
        [-76.90, 39.00],  # Northeast
        [-76.90, 38.80]   # Southeast
    ]
    
    # Date range for summer 2024
    date_range = {
        "start_date": "2024-07-01",
        "end_date": "2024-07-31"
    }
    
    print("🌍 Google Earth Engine Analysis Example - Washington, DC")
    print("=" * 60)
    
    # Initialize client
    client = GEEAnalysisClient()
    
    try:
        # Check capabilities
        print("\n📊 Available Analysis Capabilities:")
        capabilities = client.get_capabilities()
        for analysis in capabilities["available_analyses"]:
            print(f"  • {analysis['name']}: {analysis['description']}")
        
        # Urban Heat Island Analysis
        print("\n🔥 Urban Heat Island Analysis...")
        uhi_result = client.urban_heat_island_analysis(dc_coordinates, date_range)
        
        print(f"  UHI Intensity: {uhi_result['results']['uhi_intensity']}°C")
        print(f"  Surface Temperature Range: {uhi_result['results']['surface_temperature']['min']:.1f}°C - {uhi_result['results']['surface_temperature']['max']:.1f}°C")
        print(f"  Export Task ID: {uhi_result['export_info']['task_id']}")
        
        if uhi_result['recommendations']:
            print("  Recommendations:")
            for rec in uhi_result['recommendations']:
                print(f"    • {rec['title']}: {rec['description']}")
        
        # Green Space Optimization
        print("\n🌳 Green Space Optimization Analysis...")
        green_result = client.green_space_optimization(dc_coordinates)
        
        vegetation_pct = green_result['results']['vegetation_analysis']['vegetation_percentage']
        adequacy = green_result['results']['green_space_assessment']['adequacy_level']
        
        print(f"  Vegetation Coverage: {vegetation_pct:.1f}%")
        print(f"  Green Space Adequacy: {adequacy}")
        print(f"  Export Task ID: {green_result['export_info']['task_id']}")
        
        # Sustainable Building Zones
        print("\n🏗️ Sustainable Building Zones Analysis...")
        building_result = client.sustainable_building_zones(dc_coordinates)
        
        suitability_pct = building_result['results']['suitability_assessment']['suitable_for_construction']
        flood_risk = building_result['results']['suitability_assessment']['flood_risk_percentage']
        
        print(f"  Suitable for Construction: {suitability_pct:.1f}%")
        print(f"  Flood Risk Areas: {flood_risk:.1f}%")
        print(f"  Export Task ID: {building_result['export_info']['task_id']}")
        
        # Check export status for first task
        print("\n📥 Checking Export Status...")
        if uhi_result['export_info']['task_id']:
            status = client.check_export_status(uhi_result['export_info']['task_id'])
            print(f"  Task Status: {status['status']['state']}")
        
        print("\n✅ Analysis completed successfully!")
        print("\n📁 Results exported to Google Drive folder: 'GEE_Urban_Analysis'")
        print("   • Surface temperature map (GeoTIFF)")
        print("   • Vegetation NDVI map (GeoTIFF)")
        print("   • Building suitability map (GeoTIFF)")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {str(e)}")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")


def example_comprehensive_analysis():
    """Example comprehensive analysis"""
    
    # New York City area coordinates
    nyc_coordinates = [
        [-74.05, 40.70],  # Southwest
        [-74.05, 40.80],  # Northwest
        [-73.90, 40.80],  # Northeast
        [-73.90, 40.70]   # Southeast
    ]
    
    print("\n🌆 Comprehensive Analysis Example - New York City")
    print("=" * 60)
    
    client = GEEAnalysisClient()
    
    try:
        # Comprehensive analysis
        print("🔄 Running comprehensive analysis...")
        comprehensive_result = client.comprehensive_analysis(nyc_coordinates)
        
        # Summary metrics
        summary = comprehensive_result['summary_metrics']
        print(f"\n📊 Summary Metrics:")
        print(f"  UHI Intensity: {summary['uhi_intensity']}°C")
        print(f"  Vegetation Coverage: {summary['vegetation_percentage']:.1f}%")
        print(f"  Construction Suitability: {summary['construction_suitability']:.1f}%")
        print(f"  Overall Urban Health: {summary['overall_urban_health']}")
        
        # Integrated recommendations
        if comprehensive_result['integrated_recommendations']:
            print(f"\n💡 Integrated Recommendations:")
            for rec in comprehensive_result['integrated_recommendations']:
                print(f"  • {rec['title']}: {rec['description']}")
        
        print(f"\n📁 {comprehensive_result['export_info']['total_tasks']} maps exported to Google Drive")
        
    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {str(e)}")


def main():
    """Main function to run examples"""
    print("🚀 Google Earth Engine Analysis Examples")
    print("Make sure your FastAPI server is running: uvicorn main:app --reload")
    print("And that Google Earth Engine is properly configured.")
    
    # Wait for user confirmation
    input("\nPress Enter to continue with the examples...")
    
    # Run examples
    example_washington_dc_analysis()
    
    # Ask if user wants to run comprehensive analysis
    run_comprehensive = input("\nRun comprehensive analysis example? (y/n): ").lower().strip()
    if run_comprehensive == 'y':
        example_comprehensive_analysis()
    
    print("\n🎉 Examples completed!")
    print("\nNext steps:")
    print("1. Check your Google Drive for exported maps")
    print("2. Use the maps in GIS software or web mapping applications")
    print("3. Implement the recommendations in your urban planning projects")


if __name__ == "__main__":
    main()
