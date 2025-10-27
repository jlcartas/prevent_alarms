"""
Created on 27 jun 2025

@author: jlcartas
"""
from pymongo import MongoClient
from pymongo import ReturnDocument, errors
from config import bd_settings
from constants import constants_messages as messages
from utils.logger import LoggerSingleton

MONGO_URI = f"mongodb://{bd_settings.MONGO_HOST}:{bd_settings.MONGO_PORT}/"

logger = LoggerSingleton.get_logger(__name__)

class MongoDBConnection:
    _instances = {}  # Singleton instances

    def __new__(cls, db_name, collection_name):
        key = (db_name, collection_name)
        if key not in cls._instances:
            cls._instances[key] = super(MongoDBConnection, cls).__new__(cls)
        return cls._instances[key]

    def __init__(self, db_name, collection_name):
        if hasattr(self, '_initialized') and self._initialized:
            return  # Prevent re-initialization

        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self._initialized = False

        self.connect()
        self._initialized = True

    def connect(self):
        try:
            self.client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=bd_settings.MONGO_TIMEOUT
            )
            self.client.server_info()  # Trigger connection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"{messages.MONGO_ERR_CONNECTED} : {e}")
            raise


    def insert_one(self, document: dict):
        try:
            result = self.collection.insert_one(document)
            return result.inserted_id
        except errors.PyMongoError as e:
            logger.error(f"Error inserting document: {e}")
            raise errors.PyMongoError(messages.MONGO_ERR_INSERT)

    def find_one(self, query: dict):
        try:
            return self.collection.find_one(query)
        except errors.PyMongoError as e:
            logger.error(f"Error fetching document: {e}")
            raise
    
    def find_all(self, query: dict):
        try:
            return self.collection.find(query)
        except errors.PyMongoError as e:
            logger.error(f"Error fetching documents: {e}")
            raise

    def update_one(self, query: dict, update: dict, upsert=False):
        try:
            return self.collection.update_one(query, update, upsert=upsert)
        except errors.PyMongoError as e:
            logger.error(f"Error updating document: {e}")
            raise

    def find_and_update(self, query: dict, update: dict, upsert=False, return_document=ReturnDocument.AFTER):
        try:
            return self.collection.find_one_and_update(
                query,
                update,
                upsert=upsert,
                return_document=return_document
            )
        except errors.PyMongoError as e:
            logger.error(f"Error in find_and_update: {e}")
            raise