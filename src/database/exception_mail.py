'''
Created on 15 oct 2025

@author: jlcartas
'''
import os
from config import bd_settings
from database import mongodb as db
from utils.logger import LoggerSingleton

def get(query: dict):
    logger = LoggerSingleton.get_logger("services.utils.exception_mail.get")
    """
    Retrieve the subject from the MongoDB collection based on the provided subject string.
    
    :param query: The subject string to search for in the MongoDB collection.
    :return: The document containing the subject if found, otherwise None.
    """
    mongo_connection = db.MongoDBConnection(
        os.getenv("MONGO_DB_NAME", bd_settings.MONGO_DB_NAME), 
        os.getenv("MONGO_CONFIGURATIONS" ,bd_settings.MONGO_CONFIGURATIONS))
    
    try:
        # Query the collection for the document with the specified subject
        document = mongo_connection.find_one(query)
        return list(document.get("data", {}).values()) if document else None
    except Exception as e:
        logger.error(f"Error retrieving subject: {e}")
        return None
    