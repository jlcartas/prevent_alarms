'''
Created on 13 oct 2025

@author: jlcartas
'''
import os
from database import mongodb
from config import bd_settings
from utils.logger import LoggerSingleton

def get_patterns(query):
    logger = LoggerSingleton.get_logger("database.get_alarm_patterns")
    """
    Retrieve all alarm patterns from the MongoDB collection.
    :return: A list of all alarm pattern documents.
    """
    
    mongo_connection = mongodb.MongoDBConnection(
        os.getenv("MONGO_DB_NAME", bd_settings.MONGO_DB_NAME), 
        os.getenv("MONGO_PATTERNS", bd_settings.MONGO_PATTERNS) )
    
    try:
        document = mongo_connection.find_all(query)
        return document
    except Exception as e:
        logger.error(f"Error retrieving subject: {e}")
        return None