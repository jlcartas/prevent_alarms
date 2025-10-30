'''
Created on 23 oct 2025

@author: javier
'''
import os
from database import mongodb as db
from config import bd_settings
from utils.logger import LoggerSingleton
from models.alarms import Alarms

def save_or_update_alarm(alarm: Alarms):
    logger = LoggerSingleton.get_logger("services.utils.get_config.set")
    
    mongo_connection = db.MongoDBConnection(os.getenv("MONGO_DB_NAME", bd_settings.MONGO_DB_NAME), 
                                            os.getenv("MONGO_ALARMS", bd_settings.MONGO_ALARMS) )
    
#    alarm = alarm_data.model_dump()
    
    #principal alarm upsert and count_alarms increment
    try:
        result = mongo_connection.update_one(
            {"_id": alarm.id},
            {"$setOnInsert": {
                "device_name": alarm.device_name,
                "device_ip": str(alarm.device_ip),
                "dvr": alarm.dvr,
                "date": alarm.date,
                "count_alarms": 1,   # inicializa en 1
                "is_incident": True,
                "details": [d.model_dump() for d in alarm.details]
            }},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error saving or updating alarm: {e}")
        return None
    
    # If the alarm already existed, increment count_alarms
    if result.upserted_id is None:
        filter_query = {"_id": alarm.id}
        doc = mongo_connection.find_one(filter_query)
        if doc.get("is_incident", False):
            try:
                mongo_connection.update_one(
                    filter_query,
                    {"$inc": {"count_alarms": 1}}
                )
            except Exception as e:
                logger.error(f"Error incrementing alarm count: {e}")
                return None
        else:
            try:
                mongo_connection.update_one(
                   filter_query,
                {
                    "$inc": {"count_alarms": 1},
                    "$set": {"is_incident": True, 
                             "date": alarm.date}
                }
                )
            except Exception as e:
                logger.error(f"Error updating alarm count, is_incident and date: {e}")
                return None
        
        
        # Update details array if exists
        for detail in alarm.details:
        #detail = alarm.details[0]
            camera_name = detail.camera_name
            try:
                result = mongo_connection.update_one(
                    {"_id": alarm.id, "details.camera_name": camera_name},
                    {
                        "$inc": {"details.$.count_lost": 1},
                        "$set": {"details.$.date_lost": detail.date_lost}
                    }
                    )
            except Exception as e:
                logger.error(f"Error updating alarm detail: {e}")
                return None
            
            #if detail not found, add it
            if result.matched_count == 0:
                try:
                    result = mongo_connection.update_one(
                        {"_id": alarm.id},
                        {
                            "$push": {"details": detail.model_dump()}
                        }
                        )
                except Exception as e:
                    logger.error(f"Error adding new alarm detail: {e}")
                    return None
    
    return 1
