#!/usr/bin/env python3
"""
Google Earth Engine Setup Script
This script helps you set up Google Earth Engine authentication and configuration.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_gee_installation():
    """Check if earthengine-api is installed"""
    try:
        import ee
        print("✅ Google Earth Engine API is installed")
        return True
    except ImportError:
        print("❌ Google Earth Engine API is not installed")
        return False


def install_gee_api():
    """Install the Google Earth Engine API"""
    print("Installing Google Earth Engine API...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "earthengine-api"])
        print("✅ Google Earth Engine API installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Google Earth Engine API")
        return False


def setup_user_authentication():
    """Setup user authentication for Google Earth Engine"""
    print("\n🔐 Setting up Google Earth Engine User Authentication")
    print("This will open your browser to authenticate with Google Earth Engine")
    print("Make sure you have a Google Earth Engine account enabled.")
    
    try:
        import ee
        ee.Authenticate()
        print("✅ User authentication completed")
        return True
    except Exception as e:
        print(f"❌ User authentication failed: {str(e)}")
        return False


def setup_service_account():
    """Setup service account authentication"""
    print("\n🔐 Setting up Google Earth Engine Service Account Authentication")
    print("You'll need a Google Cloud Service Account with Earth Engine permissions")
    
    # Check if service account key file exists
    key_file = input("Enter the path to your service account key file (JSON): ").strip()
    
    if not os.path.exists(key_file):
        print(f"❌ Key file not found: {key_file}")
        return False
    
    try:
        # Read the key file to get the service account email
        with open(key_file, 'r') as f:
            key_data = json.load(f)
            service_account_email = key_data.get('client_email')
            
        if not service_account_email:
            print("❌ Invalid key file: client_email not found")
            return False
            
        print(f"✅ Service account email: {service_account_email}")
        
        # Copy key file to project directory
        project_key_file = "gee-service-account-key.json"
        import shutil
        shutil.copy2(key_file, project_key_file)
        
        # Set environment variables
        env_vars = {
            "GEE_SERVICE_ACCOUNT": service_account_email,
            "GEE_KEY_FILE": project_key_file,
            "GEE_PROJECT": input("Enter your Google Cloud Project ID: ").strip()
        }
        
        # Update .env file
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
        else:
            content = ""
            
        # Add or update GEE environment variables
        for key, value in env_vars.items():
            if f"{key}=" in content:
                # Update existing
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                        break
                content = '\n'.join(lines)
            else:
                # Add new
                content += f"\n{key}={value}\n"
                
        with open(env_file, 'w') as f:
            f.write(content)
            
        print("✅ Service account setup completed")
        print(f"✅ Environment variables added to .env file")
        return True
        
    except Exception as e:
        print(f"❌ Service account setup failed: {str(e)}")
        return False


def test_gee_connection():
    """Test Google Earth Engine connection"""
    print("\n🧪 Testing Google Earth Engine connection...")
    
    try:
        import ee
        from src.utils.config import get_settings
        
        settings = get_settings()
        
        if settings.GEE_SERVICE_ACCOUNT and settings.GEE_KEY_FILE:
            # Service account authentication
            key_file_path = os.path.join(os.getcwd(), settings.GEE_KEY_FILE)
            if os.path.exists(key_file_path):
                credentials = ee.ServiceAccountCredentials(
                    settings.GEE_SERVICE_ACCOUNT,
                    key_file_path
                )
                ee.Initialize(credentials, project=settings.GEE_PROJECT)
            else:
                print(f"❌ Key file not found: {key_file_path}")
                return False
        else:
            # User authentication
            ee.Initialize(project=settings.GEE_PROJECT)
            
        # Test with a simple operation
        test_image = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_044034_20140318")
        test_stats = test_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee.Geometry.Point([-122.4, 37.8]),
            scale=30,
            maxPixels=1e9
        )
        
        result = test_stats.getInfo()
        print("✅ Google Earth Engine connection successful")
        print(f"✅ Test operation completed: {len(result)} bands processed")
        return True
        
    except Exception as e:
        print(f"❌ Google Earth Engine connection failed: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("🌍 Google Earth Engine Setup for Urban Analysis Platform")
    print("=" * 60)
    
    # Check installation
    if not check_gee_installation():
        if not install_gee_api():
            return False
    
    # Choose authentication method
    print("\nChoose authentication method:")
    print("1. User Authentication (for development/testing)")
    print("2. Service Account Authentication (for production)")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        if not setup_user_authentication():
            return False
    elif choice == "2":
        if not setup_service_account():
            return False
    else:
        print("❌ Invalid choice")
        return False
    
    # Test connection
    if test_gee_connection():
        print("\n🎉 Google Earth Engine setup completed successfully!")
        print("\nNext steps:")
        print("1. Start your FastAPI server: uvicorn main:app --reload")
        print("2. Visit http://localhost:8000/docs to see the API documentation")
        print("3. Try the GEE analysis endpoints:")
        print("   - POST /api/v1/gee/urban-heat-island")
        print("   - POST /api/v1/gee/green-space-optimization")
        print("   - POST /api/v1/gee/sustainable-building-zones")
        print("   - POST /api/v1/gee/comprehensive-analysis")
        return True
    else:
        print("\n❌ Setup failed. Please check your configuration and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
