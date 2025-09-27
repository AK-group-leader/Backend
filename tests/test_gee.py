import ee
import os
from dotenv import load_dotenv

load_dotenv()

service_account = os.getenv('GEE_SERVICE_ACCOUNT')
key_file = os.getenv('GEE_KEY_FILE')

credentials = ee.ServiceAccountCredentials(service_account, key_file)
ee.Initialize(credentials, project=os.getenv('GEE_PROJECT'))

collection = ee.ImageCollection('GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL')
print(collection.size().getInfo())