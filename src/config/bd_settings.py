'''
Created on 8 jul 2025

@author: jlcartas
'''

# MongoDB connection string
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_TIMEOUT = 10000  # Timeout in milliseconds

MONGO_URI = "mongodb://localhost:27017"

MONGO_DB_NAME = "preventdb"
MONGO_COLLECTION_NAME = "lostconection"
MONGO_DEVICE = "device"
MONGO_ALARMS = "alarms"
MONGO_CONFIGURATIONS = "configurations"
MONGO_PATTERNS = "alarm_patterns"
MONGO_COUNTS = "counts"
# time format for date strings
DATE_FORMAT = "%d/%m/%Y"