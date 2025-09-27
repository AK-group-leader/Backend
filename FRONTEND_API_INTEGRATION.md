# Frontend API Integration Guide

## AI-Powered Sustainable Urban Planner Backend

This document provides all the API endpoints and features that your frontend needs to integrate with the backend.

## 🚀 Base URL

```
http://localhost:8000
```

## 📚 Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 API Endpoints Overview

### Health & Status

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### Core Analysis Endpoints

- `POST /api/v1/analysis/environmental-impact` - Environmental impact analysis
- `POST /api/v1/analysis/heat-absorption` - Heat absorption analysis
- `POST /api/v1/analysis/water-absorption` - Water absorption analysis

### Data Ingestion Endpoints

- `POST /api/v1/data/ingest/alphaearth` - Ingest AlphaEarth data
- `POST /api/v1/data/ingest/nasa` - Ingest NASA data
- `POST /api/v1/data/ingest/sentinel` - Ingest Sentinel data
- `POST /api/v1/data/ingest/noaa` - Ingest NOAA data
- `POST /api/v1/data/ingest/osm` - Ingest OpenStreetMap data

### Prediction Endpoints

- `POST /api/v1/predictions/air-quality` - Air quality predictions
- `POST /api/v1/predictions/temperature` - Temperature predictions
- `POST /api/v1/predictions/heat-island` - Urban heat island predictions
- `POST /api/v1/predictions/water-absorption` - Water absorption predictions

### Visualization Endpoints

- `POST /api/v1/visualization/heatmap` - Generate heatmaps
- `POST /api/v1/visualization/before-after` - Before/after scenarios
- `POST /api/v1/visualization/3d-model` - 3D environmental models

### AlphaEarth Integration

- `POST /api/v1/alphaearth/satellite-data` - Get satellite data
- `POST /api/v1/alphaearth/soil-data` - Get soil data
- `POST /api/v1/alphaearth/water-data` - Get water data
- `POST /api/v1/alphaearth/climate-data` - Get climate data

### Urban Heat Island Analysis

- `POST /api/v1/uhi/analyze` - Comprehensive UHI analysis
- `POST /api/v1/uhi/mitigation` - UHI mitigation recommendations
- `POST /api/v1/uhi/trends` - UHI trend analysis

---

## 📋 Detailed API Endpoints

### 1. Environmental Impact Analysis

#### `POST /api/v1/analysis/environmental-impact`

**Description**: Comprehensive environmental impact analysis for urban development projects.

**Request Body**:

```json
{
  "coordinates": [
    [longitude1, latitude1],
    [longitude2, latitude2],
    [longitude3, latitude3],
    [longitude4, latitude4]
  ],
  "project_type": "residential" | "commercial" | "industrial" | "mixed_use",
  "building_height": 50.0,
  "building_density": 0.7,
  "green_space_percentage": 0.3,
  "analysis_date": "2024-01-15",
  "include_predictions": true,
  "include_visualizations": true
}
```

**Response**:

```json
{
  "analysis_id": "uuid-string",
  "status": "completed",
  "results": {
    "heat_impact": {
      "temperature_increase": 2.5,
      "heat_absorption": 0.8,
      "urban_heat_island_effect": "moderate"
    },
    "water_impact": {
      "runoff_increase": 0.3,
      "absorption_decrease": 0.4,
      "flood_risk": "low"
    },
    "air_quality": {
      "pollution_increase": 0.15,
      "air_quality_index": "moderate"
    },
    "recommendations": [
      "Add 20% more green space",
      "Install green rooftops",
      "Use permeable paving materials"
    ]
  },
  "predictions": {
    "temperature_trends": [25.0, 25.5, 26.0, 26.5, 27.0],
    "air_quality_trends": [45, 48, 52, 55, 58]
  },
  "visualizations": {
    "heatmap_url": "/api/v1/visualization/heatmap/analysis_id",
    "before_after_url": "/api/v1/visualization/before-after/analysis_id"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Data Ingestion

#### `POST /api/v1/data/ingest/alphaearth`

**Description**: Ingest environmental data from AlphaEarth platform.

**Request Body**:

```json
{
  "coordinates": [
    [longitude1, latitude1],
    [longitude2, latitude2]
  ],
  "data_types": ["satellite", "soil", "water", "climate"],
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "resolution": "high" | "medium" | "low"
}
```

**Response**:

```json
{
  "ingestion_id": "uuid-string",
  "status": "completed",
  "data_summary": {
    "satellite_images": 15,
    "soil_samples": 8,
    "water_measurements": 12,
    "climate_records": 31
  },
  "data_tables": [
    "alphaearth_satellite_20240115_103000",
    "alphaearth_soil_20240115_103000",
    "alphaearth_water_20240115_103000",
    "alphaearth_climate_20240115_103000"
  ],
  "ingestion_time": "2024-01-15T10:30:00Z"
}
```

### 3. Predictions

#### `POST /api/v1/predictions/air-quality`

**Description**: Predict air quality impact of urban development.

**Request Body**:

```json
{
  "coordinates": [
    [longitude1, latitude1],
    [longitude2, latitude2]
  ],
  "project_parameters": {
    "building_height": 50.0,
    "building_density": 0.7,
    "traffic_increase": 0.3,
    "green_space": 0.3
  },
  "time_horizon": "1_year" | "5_years" | "10_years",
  "include_confidence_intervals": true
}
```

**Response**:

```json
{
  "prediction_id": "uuid-string",
  "time_horizon": "1_year",
  "predictions": {
    "pm2_5": {
      "current": 25.0,
      "predicted": 32.5,
      "change_percent": 30.0,
      "confidence_interval": [28.0, 37.0]
    },
    "pm10": {
      "current": 35.0,
      "predicted": 45.0,
      "change_percent": 28.6,
      "confidence_interval": [40.0, 50.0]
    },
    "no2": {
      "current": 20.0,
      "predicted": 28.0,
      "change_percent": 40.0,
      "confidence_interval": [25.0, 31.0]
    }
  },
  "health_impact": {
    "risk_level": "moderate",
    "recommendations": [
      "Install air filtration systems",
      "Increase green space by 15%",
      "Implement traffic management"
    ]
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 4. Visualizations

#### `POST /api/v1/visualization/heatmap`

**Description**: Generate environmental impact heatmaps.

**Request Body**:

```json
{
  "analysis_id": "uuid-string",
  "visualization_type": "temperature" | "air_quality" | "water_absorption" | "heat_island",
  "style": "default" | "satellite" | "terrain",
  "opacity": 0.7,
  "color_scheme": "viridis" | "plasma" | "inferno" | "magma"
}
```

**Response**:

```json
{
  "visualization_id": "uuid-string",
  "type": "heatmap",
  "data": {
    "image_url": "/static/visualizations/heatmap_analysis_id.png",
    "tile_url": "/api/v1/visualization/tiles/analysis_id/{z}/{x}/{y}.png",
    "bounds": {
      "north": 40.7589,
      "south": 40.7489,
      "east": -73.9857,
      "west": -73.9957
    },
    "legend": {
      "min_value": 20.0,
      "max_value": 35.0,
      "unit": "°C",
      "color_scale": "viridis"
    }
  },
  "metadata": {
    "resolution": "high",
    "generated_at": "2024-01-15T10:30:00Z",
    "data_sources": ["alphaearth", "nasa", "noaa"]
  }
}
```

### 5. AlphaEarth Integration

#### `POST /api/v1/alphaearth/satellite-data`

**Description**: Get real-time satellite data from AlphaEarth.

**Request Body**:

```json
{
  "coordinates": [
    [longitude1, latitude1],
    [longitude2, latitude2]
  ],
  "satellite_type": "landsat" | "sentinel" | "modis",
  "bands": ["red", "green", "blue", "nir", "swir"],
  "date": "2024-01-15",
  "cloud_coverage": 0.1
}
```

**Response**:

```json
{
  "satellite_data": {
    "image_url": "https://alphaearth.com/images/satellite_20240115.png",
    "metadata": {
      "satellite": "Landsat-8",
      "acquisition_date": "2024-01-15T10:30:00Z",
      "resolution": "30m",
      "cloud_coverage": 0.05,
      "sun_elevation": 45.2,
      "sun_azimuth": 135.8
    },
    "indices": {
      "ndvi": 0.65,
      "ndwi": 0.32,
      "ndbi": 0.15,
      "surface_temperature": 28.5
    },
    "land_cover": {
      "vegetation": 0.45,
      "urban": 0.35,
      "water": 0.15,
      "bare_soil": 0.05
    }
  },
  "processing_info": {
    "processing_time": "2.3s",
    "algorithms_used": ["ndvi", "land_cover_classification"],
    "confidence": 0.92
  }
}
```

### 6. Urban Heat Island Analysis

#### `POST /api/v1/uhi/analyze`

**Description**: Comprehensive urban heat island analysis.

**Request Body**:

```json
{
  "coordinates": [
    [longitude1, latitude1],
    [longitude2, latitude2]
  ],
  "analysis_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "include_temporal_analysis": true,
  "include_spatial_analysis": true,
  "comparison_areas": [
    {
      "name": "rural_reference",
      "coordinates": [[longitude3, latitude3], [longitude4, latitude4]]
    }
  ]
}
```

**Response**:

```json
{
  "uhi_analysis_id": "uuid-string",
  "uhi_intensity": {
    "maximum": 4.2,
    "average": 2.8,
    "minimum": 1.5,
    "unit": "°C"
  },
  "temporal_analysis": {
    "daily_pattern": {
      "peak_hour": 14,
      "peak_temperature": 32.5,
      "cooling_rate": 0.8
    },
    "seasonal_pattern": {
      "summer_intensity": 4.2,
      "winter_intensity": 1.8,
      "spring_intensity": 2.5,
      "autumn_intensity": 2.9
    }
  },
  "spatial_analysis": {
    "hot_spots": [
      {
        "coordinates": [longitude, latitude],
        "intensity": 4.2,
        "area_type": "commercial_center"
      }
    ],
    "cool_spots": [
      {
        "coordinates": [longitude, latitude],
        "intensity": 1.5,
        "area_type": "park"
      }
    ]
  },
  "mitigation_recommendations": [
    {
      "type": "green_roofs",
      "potential_reduction": 1.2,
      "cost_estimate": 50000,
      "implementation_time": "6_months"
    },
    {
      "type": "tree_planting",
      "potential_reduction": 0.8,
      "cost_estimate": 25000,
      "implementation_time": "3_months"
    }
  ]
}
```

---

## 🎨 Frontend Integration Examples

### React/JavaScript Example

```javascript
// Environmental Impact Analysis
const analyzeEnvironmentalImpact = async (coordinates, projectData) => {
  const response = await fetch(
    "http://localhost:8000/api/v1/analysis/environmental-impact",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        coordinates: coordinates,
        project_type: projectData.type,
        building_height: projectData.height,
        building_density: projectData.density,
        green_space_percentage: projectData.greenSpace,
        analysis_date: new Date().toISOString().split("T")[0],
        include_predictions: true,
        include_visualizations: true,
      }),
    }
  );

  return await response.json();
};

// Get Satellite Data
const getSatelliteData = async (coordinates) => {
  const response = await fetch(
    "http://localhost:8000/api/v1/alphaearth/satellite-data",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        coordinates: coordinates,
        satellite_type: "landsat",
        bands: ["red", "green", "blue", "nir"],
        date: new Date().toISOString().split("T")[0],
        cloud_coverage: 0.1,
      }),
    }
  );

  return await response.json();
};

// Generate Heatmap
const generateHeatmap = async (analysisId, visualizationType) => {
  const response = await fetch(
    "http://localhost:8000/api/v1/visualization/heatmap",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        analysis_id: analysisId,
        visualization_type: visualizationType,
        style: "satellite",
        opacity: 0.7,
        color_scheme: "viridis",
      }),
    }
  );

  return await response.json();
};
```

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def analyze_environmental_impact(coordinates, project_data):
    """Analyze environmental impact of a project"""
    url = f"{BASE_URL}/api/v1/analysis/environmental-impact"
    payload = {
        "coordinates": coordinates,
        "project_type": project_data["type"],
        "building_height": project_data["height"],
        "building_density": project_data["density"],
        "green_space_percentage": project_data["green_space"],
        "analysis_date": "2024-01-15",
        "include_predictions": True,
        "include_visualizations": True
    }

    response = requests.post(url, json=payload)
    return response.json()

def get_satellite_data(coordinates):
    """Get satellite data from AlphaEarth"""
    url = f"{BASE_URL}/api/v1/alphaearth/satellite-data"
    payload = {
        "coordinates": coordinates,
        "satellite_type": "landsat",
        "bands": ["red", "green", "blue", "nir"],
        "date": "2024-01-15",
        "cloud_coverage": 0.1
    }

    response = requests.post(url, json=payload)
    return response.json()
```

---

## 🗺️ Map Integration

### Leaflet.js Integration

```javascript
// Add heatmap layer to map
const addHeatmapLayer = (map, analysisId) => {
  const heatmapUrl = `http://localhost:8000/api/v1/visualization/tiles/${analysisId}/{z}/{x}/{y}.png`;

  const heatmapLayer = L.tileLayer(heatmapUrl, {
    opacity: 0.7,
    attribution: "Environmental Impact Heatmap",
  });

  heatmapLayer.addTo(map);
};

// Display satellite imagery
const addSatelliteLayer = (map, satelliteData) => {
  const bounds = L.latLngBounds(
    [satelliteData.metadata.bounds.south, satelliteData.metadata.bounds.west],
    [satelliteData.metadata.bounds.north, satelliteData.metadata.bounds.east]
  );

  const satelliteLayer = L.imageOverlay(satelliteData.image_url, bounds, {
    opacity: 0.8,
  });

  satelliteLayer.addTo(map);
  map.fitBounds(bounds);
};
```

---

## 📊 Data Visualization Components

### Chart.js Integration

```javascript
// Temperature trend chart
const createTemperatureChart = (predictions) => {
  const ctx = document.getElementById("temperatureChart").getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: predictions.time_horizon,
      datasets: [
        {
          label: "Temperature (°C)",
          data: predictions.temperature_trends,
          borderColor: "rgb(255, 99, 132)",
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: "Temperature (°C)",
          },
        },
      },
    },
  });
};

// Air quality gauge
const createAirQualityGauge = (airQualityData) => {
  const ctx = document.getElementById("airQualityGauge").getContext("2d");

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Good", "Moderate", "Unhealthy"],
      datasets: [
        {
          data: [
            airQualityData.good,
            airQualityData.moderate,
            airQualityData.unhealthy,
          ],
          backgroundColor: ["#4CAF50", "#FF9800", "#F44336"],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });
};
```

---

## 🔧 Error Handling

### Common Error Responses

```json
{
  "error": {
    "code": 400,
    "message": "Invalid coordinates provided",
    "type": "ValidationError",
    "details": {
      "field": "coordinates",
      "issue": "Coordinates must be valid longitude/latitude pairs"
    }
  }
}
```

### Error Handling in Frontend

```javascript
const handleApiError = (error, response) => {
  if (response.status === 400) {
    console.error("Validation Error:", response.error.message);
    // Show user-friendly validation message
  } else if (response.status === 404) {
    console.error("Not Found:", response.error.message);
    // Handle not found case
  } else if (response.status === 500) {
    console.error("Server Error:", response.error.message);
    // Show generic error message
  }
};

const safeApiCall = async (apiFunction, ...args) => {
  try {
    const result = await apiFunction(...args);
    return { success: true, data: result };
  } catch (error) {
    handleApiError(error, error.response);
    return { success: false, error: error.response?.data || error.message };
  }
};
```

---

## 🚀 Getting Started

1. **Start the Backend Server**:

   ```bash
   cd Backend
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Test API Connection**:

   ```bash
   curl http://localhost:8000/health
   ```

3. **Explore API Documentation**:

   - Visit http://localhost:8000/docs for interactive API testing

4. **Integrate with Frontend**:
   - Use the provided examples above
   - Handle errors gracefully
   - Implement loading states for async operations

---

## 📝 Notes for Frontend Developers

- **All endpoints return JSON**
- **Use POST for data submission and analysis**
- **Coordinates should be in [longitude, latitude] format**
- **Include proper error handling for network requests**
- **Implement loading states for better UX**
- **Cache visualization results when possible**
- **Use the interactive docs at /docs for testing**

This backend provides a complete environmental impact analysis platform with real-time data integration, ML predictions, and advanced visualizations. All endpoints are designed to be frontend-friendly with consistent response formats and comprehensive error handling.
