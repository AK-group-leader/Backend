# AI-Powered Sustainable Urban Planner

A comprehensive platform for analyzing environmental impact of urban development using satellite imagery, soil and water data, and AI models to predict the environmental impact of new construction.

## 🌍 Overview

Developing cities often face rising temperatures due to the **Urban Heat Island (UHI) effect** - areas within cities that experience higher temperatures than their surrounding rural regions due to human activities and urban infrastructure.

### 🔥 **Urban Heat Island Challenge**

Urban Heat Islands are caused by:

- **Heat-absorbing materials** like concrete and asphalt that store heat during the day and release it slowly at night
- **Lack of vegetation** that would provide cooling through evapotranspiration
- **Anthropogenic heat** from vehicles, buildings, and industrial activities
- **Reduced air circulation** due to urban canyon effects

### 📊 **UHI Impacts We Address**

- **Energy Consumption**: Increased cooling demand leading to higher electricity costs
- **Air Quality**: Higher temperatures worsen air pollution and ozone formation
- **Public Health**: Heat-related illnesses, especially affecting vulnerable populations
- **Economic Burden**: Significant costs to communities and healthcare systems

Our solution is a web platform that uses satellite imagery, soil and water data, and AI models to predict the environmental impact of new construction and provide actionable mitigation strategies.

## ✨ Features

### 🔬 Environmental Impact Analysis

- **Urban Heat Island Analysis**: Comprehensive UHI impact assessment including energy consumption, air quality, and public health
- **Heat Island Effect Prediction**: Predict temperature rise and heat absorption risks
- **Water Absorption Analysis**: Analyze flood risk and drainage efficiency
- **Air Quality Impact Assessment**: Predict air quality changes and pollutant concentrations
- **Comprehensive Environmental Analysis**: Combined analysis of all environmental factors

### 📊 Data Integration

- **AlphaEarth**: Primary data source for satellite, soil, water, and climate data
- **NASA EarthData**: Satellite imagery and environmental data
- **Sentinel Hub**: European Space Agency satellite data
- **NOAA**: Weather and climate data
- **OpenStreetMap**: Open source mapping data

### 🤖 AI/ML Predictions

- **Machine Learning Models**: Predict heat absorption, temperature rise, and soil/water absorption risks
- **Confidence Intervals**: Statistical confidence levels for all predictions
- **Time Horizon Analysis**: Predictions for 1-50 year timeframes
- **Model Training**: Continuous model improvement and retraining

### 🗺️ Interactive Visualizations

- **Heatmaps**: Temperature, air quality, water absorption, and population density
- **Before/After Scenarios**: Compare baseline vs proposed development scenarios
- **Time Series Charts**: Track environmental trends over time
- **3D Models**: Terrain and building models for spatial analysis

### 🌱 Sustainability Recommendations

- **UHI Mitigation Strategies**: Green roofs, urban forests, cool pavements, and water features
- **Eco-friendly Alternatives**: Suggest green rooftops, tree cover, and water bodies
- **Mitigation Strategies**: Reduce heat and improve sustainability
- **Cost-Benefit Analysis**: Implementation costs and environmental benefits
- **Priority Ranking**: Recommendations sorted by impact and feasibility

## 🏗️ Architecture

### Backend (FastAPI + Databricks)

- **FastAPI**: RESTful API with automatic documentation
- **Databricks**: Data processing and ML model training
- **PostgreSQL**: Data storage and caching
- **Redis**: Session management and caching

### Frontend (React + Mapbox)

- **React**: Modern web interface
- **Mapbox**: Interactive mapping and visualization
- **Real-time Updates**: Live environmental impact analysis

### Data Sources

- **AlphaEarth**: Comprehensive environmental data platform with real-time satellite, soil, water, and climate data
- **NASA EarthData**: Landsat, MODIS, Sentinel-2 data
- **Sentinel Hub**: High-resolution satellite imagery
- **NOAA**: Weather and climate datasets
- **OpenStreetMap**: Building, road, and landuse data

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Databricks Account** (for data storage and ML processing)
3. **Redis** (for caching, optional)
4. **PostgreSQL** (optional, for additional local storage)
5. **API Keys** for data sources:
   - AlphaEarth API key (primary data source)
   - NASA EarthData API key
   - Sentinel Hub API key
   - NOAA API key (optional)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Backend
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**

```bash
   cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database (using Databricks as primary - DATABASE_URL is optional)
# DATABASE_URL=postgresql://user:password@localhost:5432/urban_planner

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Databricks (required for data storage and ML processing)
DATABRICKS_HOST=your-databricks-host
DATABRICKS_TOKEN=your-databricks-token
DATABRICKS_WAREHOUSE_ID=your-warehouse-id

# API Keys
ALPHAEARTH_API_KEY=your-alphaearth-api-key
NASA_API_KEY=your-nasa-api-key
SENTINEL_API_KEY=your-sentinel-api-key
NOAA_API_KEY=your-noaa-api-key

# Application
DEBUG=False
LOG_LEVEL=INFO
```

5. **Start the server:**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Environmental Analysis

- `POST /api/v1/analysis/environmental-impact` - Comprehensive environmental analysis
- `GET /api/v1/analysis/heat-island/{analysis_id}` - Get heat island analysis results
- `GET /api/v1/analysis/water-absorption/{analysis_id}` - Get water absorption analysis
- `POST /api/v1/analysis/compare-scenarios` - Compare baseline vs proposed scenarios

#### Data Ingestion

- `POST /api/v1/data/ingest` - Ingest data from external sources
- `GET /api/v1/data/sources` - Get available data sources
- `GET /api/v1/data/ingestion-status/{ingestion_id}` - Get ingestion status
- `GET /api/v1/data/data-catalog` - Get data catalog

#### ML Predictions

- `POST /api/v1/predictions/predict` - Make ML predictions
- `POST /api/v1/predictions/batch-predict` - Batch predictions
- `GET /api/v1/predictions/models` - Get available models
- `POST /api/v1/predictions/model-training` - Train/retrain models

#### Visualizations

- `POST /api/v1/visualization/heatmap` - Generate heatmap visualizations
- `POST /api/v1/visualization/before-after` - Generate before/after comparisons
- `POST /api/v1/visualization/time-series` - Generate time series charts
- `POST /api/v1/visualization/3d-model` - Generate 3D models

#### AlphaEarth Integration

- `POST /api/v1/alphaearth/data/ingest` - Ingest data from AlphaEarth API
- `POST /api/v1/alphaearth/heatmap` - Generate heatmaps using AlphaEarth data
- `POST /api/v1/alphaearth/sustainability-score` - Calculate sustainability scores
- `GET /api/v1/alphaearth/data/status` - Get AlphaEarth data status

#### Urban Heat Island Analysis

- `POST /api/v1/uhi/comprehensive-analysis` - Comprehensive UHI analysis including energy, air quality, and health impacts
- `POST /api/v1/uhi/mitigation-analysis` - Analyze UHI mitigation strategies and their effectiveness
- `POST /api/v1/uhi/scenario-comparison` - Compare UHI impacts between baseline and proposed scenarios
- `GET /api/v1/uhi/mitigation-strategies` - Get available UHI mitigation strategies
- `GET /api/v1/uhi/uhi-impacts/{analysis_id}` - Get detailed UHI impact breakdown

## 🔧 Configuration

### Environment Variables

| Variable             | Description               | Default   |
| -------------------- | ------------------------- | --------- |
| `HOST`               | API host                  | `0.0.0.0` |
| `PORT`               | API port                  | `8000`    |
| `DEBUG`              | Debug mode                | `False`   |
| `DATABASE_URL`       | Database connection URL   | Required  |
| `REDIS_URL`          | Redis connection URL      | Required  |
| `DATABRICKS_HOST`    | Databricks workspace host | Optional  |
| `DATABRICKS_TOKEN`   | Databricks access token   | Optional  |
| `ALPHAEARTH_API_KEY` | AlphaEarth API key        | Required  |
| `NASA_API_KEY`       | NASA EarthData API key    | Optional  |
| `SENTINEL_API_KEY`   | Sentinel Hub API key      | Optional  |
| `NOAA_API_KEY`       | NOAA API key              | Optional  |

### Data Storage

- **Raw Data**: `data/raw/` - Ingested data from external sources
- **Processed Data**: `data/processed/` - Cleaned and processed data
- **ML Models**: `data/models/` - Trained ML models
- **Static Files**: `static/` - Images and icons

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_analysis.py
```

## 📊 Example Usage

### 1. Environmental Impact Analysis

```python
import requests

# Analyze environmental impact
response = requests.post("http://localhost:8000/api/v1/analysis/environmental-impact", json={
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "analysis_type": "comprehensive",
    "time_horizon": 10,
    "include_recommendations": True
})

analysis_results = response.json()
print(f"Overall risk score: {analysis_results['results']['overall_risk_score']}")
```

### 2. Data Ingestion

```python
# Ingest data from NASA
response = requests.post("http://localhost:8000/api/v1/data/ingest", json={
    "data_source": "nasa",
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "date_range": {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    },
    "data_types": ["landsat", "modis"]
})

ingestion_results = response.json()
print(f"Records ingested: {ingestion_results['records_ingested']}")
```

### 3. Generate Heatmap

```python
# Generate temperature heatmap
response = requests.post("http://localhost:8000/api/v1/visualization/heatmap", json={
    "data_type": "temperature",
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "resolution": 100,
    "color_scheme": "viridis"
})

heatmap_data = response.json()
print(f"Heatmap generated: {heatmap_data['heatmap_id']}")
```

### 4. AlphaEarth Integration

```python
# Ingest data from AlphaEarth
response = requests.post("http://localhost:8000/api/v1/alphaearth/data/ingest", json={
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "data_types": ["satellite", "soil", "water", "climate"],
    "resolution": "high"
})

ingestion_result = response.json()
print(f"AlphaEarth data ingested: {ingestion_result['records_ingested']} records")

# Generate heatmap using AlphaEarth data
response = requests.post("http://localhost:8000/api/v1/alphaearth/heatmap", json={
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "data_type": "temperature",
    "resolution": 100
})

heatmap_data = response.json()
print(f"AlphaEarth heatmap generated: {heatmap_data['heatmap_id']}")

# Calculate sustainability score
response = requests.post("http://localhost:8000/api/v1/alphaearth/sustainability-score", json={
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "include_recommendations": True
})

sustainability_result = response.json()
print(f"Sustainability score: {sustainability_result['sustainability_score']['overall_score']}")
print(f"Grade: {sustainability_result['sustainability_score']['grade']}")
```

### 5. Urban Heat Island Analysis

```python
# Comprehensive UHI analysis
response = requests.post("http://localhost:8000/api/v1/uhi/comprehensive-analysis", json={
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "time_horizon": 10,
    "include_mitigation": True,
    "include_economic_impact": True
})

uhi_analysis = response.json()
print(f"UHI intensity: {uhi_analysis['results']['uhi_intensity']['temperature_difference']}°C")
print(f"Energy impact: {uhi_analysis['results']['energy_consumption_impact']['additional_energy_cost_usd']} USD")
print(f"Health impact: {uhi_analysis['results']['public_health_impact']['heat_related_health_impacts']['total_healthcare_cost_usd']} USD")

# UHI mitigation analysis
response = requests.post("http://localhost:8000/api/v1/uhi/mitigation-analysis", json={
    "coordinates": [[-74.0059, 40.7128], [-74.0059, 40.7589], [-73.9352, 40.7589], [-73.9352, 40.7128]],
    "mitigation_strategies": ["green_roofs", "urban_forests", "cool_pavements"],
    "priority_focus": "energy_savings"
})

mitigation_analysis = response.json()
print(f"Temperature reduction potential: {mitigation_analysis['mitigation_analysis']['achievable_temperature_reduction']}°C")
print(f"Payback period: {mitigation_analysis['mitigation_analysis']['cost_analysis']['payback_period_years']} years")
```

## 🌱 Sustainability Impact

This platform helps cities plan sustainable growth by:

- **Reducing Urban Heat Islands**: Identify areas at risk and suggest mitigation strategies
- **Improving Water Management**: Predict flood risks and optimize drainage systems
- **Enhancing Air Quality**: Monitor and predict air pollution impacts
- **Promoting Green Infrastructure**: Recommend eco-friendly development alternatives
- **Supporting Data-Driven Decisions**: Provide evidence-based environmental impact assessments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NASA** for Earth observation data
- **European Space Agency** for Sentinel satellite data
- **NOAA** for weather and climate data
- **OpenStreetMap** contributors for open mapping data
- **Databricks** for ML platform capabilities

## 📞 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the documentation at `/docs`

---

**Built with ❤️ for sustainable urban development**
