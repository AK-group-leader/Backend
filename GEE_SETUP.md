# Google Earth Engine Integration Setup

This guide will help you set up Google Earth Engine integration for the Urban Analysis Platform, enabling advanced satellite-based environmental analysis.

## 🌟 Features

The Google Earth Engine integration provides:

- **Urban Heat Island Mapping** - Detect hotspots using Landsat surface temperature
- **Green Space Optimization** - Analyze vegetation distribution vs population density  
- **Sustainable Building Zones** - Multi-criteria analysis for construction planning
- **Comprehensive Urban Analysis** - Combined analysis of all three aspects

## 📋 Prerequisites

1. **Google Earth Engine Account**: You need a Google Earth Engine account with access enabled
2. **Google Cloud Project**: A Google Cloud project with Earth Engine API enabled
3. **Python Environment**: Python 3.8+ with the required dependencies

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

Run the setup script which will guide you through the process:

```bash
python setup_gee.py
```

This script will:
- Check if `earthengine-api` is installed
- Install it if missing
- Guide you through authentication setup
- Test the connection
- Configure environment variables

### Option 2: Manual Setup

#### Step 1: Install Dependencies

```bash
pip install earthengine-api
```

#### Step 2: Authentication

Choose one of the authentication methods:

##### User Authentication (Development/Testing)

```bash
earthengine authenticate
```

This will open your browser to authenticate with Google Earth Engine.

##### Service Account Authentication (Production)

1. Create a service account in Google Cloud Console
2. Enable Earth Engine API for your project
3. Add the service account to your Earth Engine project
4. Download the JSON key file
5. Set environment variables:

```bash
export GEE_SERVICE_ACCOUNT="your-service-account@project.iam.gserviceaccount.com"
export GEE_KEY_FILE="path/to/your/key.json"
export GEE_PROJECT="your-google-cloud-project-id"
```

#### Step 3: Test Connection

```python
import ee
ee.Initialize()
print("Google Earth Engine initialized successfully!")
```

## 🔧 Environment Variables

Add these to your `.env` file:

```env
# Google Earth Engine Configuration
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_KEY_FILE=gee-service-account-key.json
GEE_PROJECT=your-google-cloud-project-id
```

## 📊 API Endpoints

Once set up, you can use these endpoints:

### Urban Heat Island Analysis
```http
POST /api/v1/gee/urban-heat-island
```

**Request Body:**
```json
{
  "coordinates": [[-77.12, 38.80], [-77.12, 39.00], [-76.90, 39.00], [-76.90, 38.80]],
  "date_range": {
    "start_date": "2024-07-01",
    "end_date": "2024-07-31"
  },
  "include_recommendations": true
}
```

**Response:**
- Surface temperature analysis
- UHI intensity calculation
- Vegetation and built-up indices
- Cooling recommendations
- Export task ID for map download

### Green Space Optimization
```http
POST /api/v1/gee/green-space-optimization
```

**Request Body:**
```json
{
  "coordinates": [[-77.12, 38.80], [-77.12, 39.00], [-76.90, 39.00], [-76.90, 38.80]],
  "population_density_threshold": 5000.0
}
```

**Response:**
- Vegetation analysis (NDVI)
- Land cover classification
- Population density correlation
- Optimization recommendations

### Sustainable Building Zones
```http
POST /api/v1/gee/sustainable-building-zones
```

**Request Body:**
```json
{
  "coordinates": [[-77.12, 38.80], [-77.12, 39.00], [-76.90, 39.00], [-76.90, 38.80]],
  "include_risk_assessment": true
}
```

**Response:**
- Terrain analysis (elevation, slope)
- Soil and water analysis
- Air quality assessment
- Suitability scoring
- Risk assessment (flood, erosion)

### Comprehensive Analysis
```http
POST /api/v1/gee/comprehensive-analysis
```

**Request Body:**
```json
{
  "coordinates": [[-77.12, 38.80], [-77.12, 39.00], [-76.90, 39.00], [-76.90, 38.80]],
  "analysis_type": "comprehensive"
}
```

**Response:**
- All three analyses combined
- Integrated recommendations
- Summary metrics
- Multiple export tasks

### Check Export Status
```http
GET /api/v1/gee/export-status/{task_id}
```

Check if your exported maps are ready for download from Google Drive.

## 🗺️ Data Sources

The analysis uses these satellite datasets:

- **Landsat-9**: Surface temperature, vegetation indices (NDVI, NDBI)
- **Sentinel-5P**: Air quality (NO2)
- **SRTM**: Digital elevation model
- **WorldPop**: Population density

## 📁 Export Information

All analysis results are exported to your Google Drive in the `GEE_Urban_Analysis` folder:

- **Format**: GeoTIFF
- **Resolution**: 30m
- **Coordinate System**: EPSG:4326 (WGS84)
- **Folder**: `GEE_Urban_Analysis/`

## 🔍 Analysis Capabilities

### Urban Heat Island Mapping
- **Purpose**: Detect hotspots where cooling strategies are needed
- **Data**: Landsat-9 surface temperature
- **Outputs**: Temperature maps, UHI intensity, cooling recommendations
- **Applications**: Tree planting locations, reflective roof placement

### Green Space Optimization
- **Purpose**: Identify areas lacking vegetation vs population density
- **Data**: Landsat-9 NDVI, WorldPop population
- **Outputs**: Vegetation maps, land cover classification, optimization recommendations
- **Applications**: Park placement, green infrastructure planning

### Sustainable Building Zones
- **Purpose**: Plan construction that won't worsen flooding/erosion
- **Data**: SRTM elevation, Landsat soil moisture, Sentinel-5P air quality
- **Outputs**: Suitability maps, risk assessments, construction recommendations
- **Applications**: Site selection, risk mitigation planning

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   Solution: Run `earthengine authenticate` or check service account permissions
   ```

2. **Project Not Found**
   ```
   Solution: Ensure GEE_PROJECT matches your Google Cloud project ID
   ```

3. **No Data Available**
   ```
   Solution: Try expanding the date range or selecting a different area
   ```

4. **Export Failures**
   ```
   Solution: Check Google Drive permissions and available storage space
   ```

### Getting Help

1. Check the [Google Earth Engine documentation](https://developers.google.com/earth-engine)
2. Visit the [Earth Engine Community](https://groups.google.com/g/google-earthengine)
3. Review the API logs for detailed error messages

## 🚀 Example Usage

### Python Client Example

```python
import requests

# Urban Heat Island Analysis
response = requests.post(
    "http://localhost:8000/api/v1/gee/urban-heat-island",
    json={
        "coordinates": [[-77.12, 38.80], [-77.12, 39.00], [-76.90, 39.00], [-76.90, 38.80]],
        "date_range": {
            "start_date": "2024-07-01",
            "end_date": "2024-07-31"
        }
    }
)

result = response.json()
print(f"UHI Intensity: {result['results']['uhi_intensity']}°C")
print(f"Export Task ID: {result['export_info']['task_id']}")
```

### Frontend Integration Example

```javascript
// Urban Heat Island Analysis
const analyzeUHI = async (coordinates) => {
  const response = await fetch('/api/v1/gee/urban-heat-island', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      coordinates: coordinates,
      include_recommendations: true
    })
  });
  
  const result = await response.json();
  return result;
};

// Use with Leaflet/Mapbox for visualization
const displayResults = (results) => {
  // Display temperature map
  // Show recommendations
  // Update UI with analysis results
};
```

## 📈 Performance Considerations

- **Area Limit**: Maximum 100 km² per analysis
- **Processing Time**: 30-60 seconds per analysis
- **Export Time**: 2-5 minutes for map generation
- **Rate Limits**: Google Earth Engine has usage quotas

## 🔒 Security Notes

- Keep service account keys secure
- Use environment variables for sensitive data
- Regularly rotate service account keys
- Monitor usage and quotas

## 🎯 Next Steps

1. Set up authentication using the setup script
2. Test with a small area first
3. Explore the API documentation at `/docs`
4. Integrate with your frontend application
5. Monitor export tasks and download results

Happy analyzing! 🌍✨
