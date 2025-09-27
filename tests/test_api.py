"""
Basic API tests
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AI-Powered Sustainable Urban Planner" in data["message"]


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analysis_endpoints_exist():
    """Test that analysis endpoints exist"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_data_sources_endpoint():
    """Test data sources endpoint"""
    response = client.get("/api/v1/data/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert len(data["sources"]) > 0


def test_models_endpoint():
    """Test models endpoint"""
    response = client.get("/api/v1/predictions/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0


def test_visualization_types_endpoint():
    """Test visualization types endpoint"""
    response = client.get("/api/v1/visualization/visualization-types")
    assert response.status_code == 200
    data = response.json()
    assert "visualization_types" in data
    assert len(data["visualization_types"]) > 0
