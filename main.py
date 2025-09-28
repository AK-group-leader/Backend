"""
AI-Powered Sustainable Urban Planner
FastAPI Backend for Environmental Impact Analysis
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from pathlib import Path

from src.api.routes import analysis, data_ingestion, predictions, visualization, alphaearth, uhi_analysis, gee_analysis, chatbot
from src.utils.config import get_settings
from src.utils.database import init_database
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AI-Powered Sustainable Urban Planner API")
    await init_database()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down AI-Powered Sustainable Urban Planner API")


# Create FastAPI app
app = FastAPI(
    title="AI-Powered Sustainable Urban Planner",
    description="""
    A comprehensive platform for analyzing environmental impact of urban development with Google Earth Engine integration.
    
    ## Features
    
    * **Urban Heat Island Mapping**: Detect hotspots where planting trees or adding reflective roofs reduces warming
    * **Green Space Optimization**: Identify areas lacking vegetation vs high population density
    * **Sustainable Building Zones**: Combine soil/water data to plan construction that won't worsen flooding/erosion
    * **Environmental Impact Analysis**: Predict heat absorption, temperature rise, and soil/water absorption risks
    * **Data Integration**: Ingest data from Google Earth Engine, NASA EarthData, Sentinel Hub, NOAA, and OpenStreetMap
    * **AI/ML Predictions**: Use machine learning models to predict environmental outcomes
    * **Interactive Visualizations**: Generate heatmaps and before/after scenarios
    * **Sustainability Recommendations**: Suggest eco-friendly alternatives like green rooftops and tree cover
    
    ## Google Earth Engine Analysis
    
    * **Urban Heat Island**: Landsat-9 surface temperature analysis
    * **Green Space**: NDVI analysis with population density correlation
    * **Sustainable Zones**: Multi-criteria analysis combining terrain, soil, water, and air quality
    
    ## Data Sources
    
    * Google Earth Engine (Landsat-9, Sentinel-5P, SRTM, WorldPop)
    * NASA EarthData
    * Sentinel Hub
    * NOAA
    * OpenStreetMap
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(data_ingestion.router,
                   prefix="/api/v1/data", tags=["Data Ingestion"])
app.include_router(predictions.router,
                   prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(visualization.router,
                   prefix="/api/v1/visualization", tags=["Visualization"])
app.include_router(alphaearth.router,
                   prefix="/api/v1/alphaearth", tags=["AlphaEarth"])
app.include_router(uhi_analysis.router,
                   prefix="/api/v1/uhi", tags=["Urban Heat Island Analysis"])
app.include_router(gee_analysis.router,
                   prefix="/api/v1/gee", tags=["Google Earth Engine Analysis"])
app.include_router(chatbot.router,
                   prefix="/api/v1/chatbot", tags=["AI Chatbot"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI-Powered Sustainable Urban Planner API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "analysis": "/api/v1/analysis",
            "data_ingestion": "/api/v1/data",
            "predictions": "/api/v1/predictions",
            "visualization": "/api/v1/visualization",
            "alphaearth": "/api/v1/alphaearth",
            "uhi_analysis": "/api/v1/uhi",
            "gee_analysis": "/api/v1/gee",
            "chatbot": "/api/v1/chatbot",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI-Powered Sustainable Urban Planner",
        "version": "1.0.0"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "InternalError"
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
