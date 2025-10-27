'''
Created on 8 jul 2025

@author: jlcartas
'''

# MongoDB messages Errrors
MONGO_ERR_CONNECTED = "Could not connect to MongoDB"
MONGO_ERR_CONNECTION = "Error connecting to MongoDB"
MONGO_ERR_TIMEOUT = "MongoDB connection timed out"
MONGO_ERR_INSERT = "Error inserting document into MongoDB"
MONGO_ERR_READ = "Error reading document from MongoDB"
MONGO_ERR_UPDATE = "Error updating document in MongoDB"
MONGO_ERR_DELETE = "Error deleting document from MongoDB"
MONGO_ERR_CLOSE = "Error closing MongoDB connection"
MONGO_ERR_ESTABLISH = "Database connection not established. Call connect() first."

# MongoDB messages Success
MONGO_SUCCESS_CONNECTION = "Successfully connected to MongoDB"

# MongoDB messages General
MONGO_ERR_GENERAL = "An error occurred with MongoDB operation"
MONGO_SUCCESS_GENERAL = "MongoDB operation completed successfully"
MONGO_CLOSE_SUCCESS = "MongoDB connection closed successfully"
MONGO_NOT_CLOSED = "MongoDB connection is not closed"

# MongoDB messages Collection
MONGO_ERR_COLLECTION_NOT_INITIALIZED = "Collection not initialized. Call connect() first."
MONGO_ERR_COLLECTION_NOT_FOUND = "Collection not found in the database"
MONGO_SUCCESS_COLLECTION_INITIALIZED = "Collection successfully initialized"
