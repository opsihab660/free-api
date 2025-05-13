"""
MongoDB client module for Vercel deployment.
This module provides a simplified version of the MongoDB connection for Vercel.
"""

import logging
import os
import traceback
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.database import Database
from decimal import Decimal
from bson import Decimal128

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global MongoDB client
client: Optional[MongoClient] = None
db: Optional[Database] = None

# Get MongoDB settings from environment variables
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "api_service_db")
MONGODB_USER_COLLECTION = os.environ.get("MONGODB_USER_COLLECTION", "users")

def decimal_to_decimal128(obj):
    """Convert Decimal objects to MongoDB Decimal128 for storage"""
    if isinstance(obj, dict):
        return {k: decimal_to_decimal128(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_decimal128(item) for item in obj]
    elif isinstance(obj, Decimal):
        return Decimal128(str(obj))
    return obj

def decimal128_to_decimal(obj):
    """Convert MongoDB Decimal128 objects back to Python Decimal"""
    if isinstance(obj, dict):
        return {k: decimal128_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal128_to_decimal(item) for item in obj]
    elif isinstance(obj, Decimal128):
        return Decimal(str(obj))
    return obj

def connect_to_mongodb():
    """Connect to MongoDB and initialize collections"""
    global client, db
    
    if not MONGODB_URI:
        logger.error("MONGODB_URI environment variable is not set")
        return False
    
    try:
        # Print debug info
        logger.info(f"Connecting to MongoDB with URI: {MONGODB_URI[:20]}...{MONGODB_URI[-10:]}")
        logger.info(f"Database name: {MONGODB_DB_NAME}")
        logger.info(f"Collection name: {MONGODB_USER_COLLECTION}")
        
        # Create MongoDB client with a timeout
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Check connection
        client.admin.command('ping')
        
        # Get database and collections
        db = client[MONGODB_DB_NAME]
        
        # Create indexes for faster lookups
        try:
            db[MONGODB_USER_COLLECTION].create_index("username", unique=True)
            db[MONGODB_USER_COLLECTION].create_index("api_key.key", unique=True, sparse=True)
            db[MONGODB_USER_COLLECTION].create_index("user_id", unique=True)
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
            # Continue anyway, indexes are not critical
        
        logger.info(f"Connected to MongoDB, database: {MONGODB_DB_NAME}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        traceback.print_exc()
        return False

def close_mongodb_connection():
    """Close the MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

def load_all_users() -> Dict[str, Any]:
    """Load all users from MongoDB and format them for the application"""
    global client, db
    
    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return {}
    
    try:
        users_dict = {}
        users_cursor = db[MONGODB_USER_COLLECTION].find({})
        
        for user in users_cursor:
            # Remove MongoDB _id field
            user.pop('_id', None)
            
            # Convert Decimal128 back to Decimal
            user = decimal128_to_decimal(user)
            
            # Use API key as the dictionary key if available
            if 'api_key' in user and 'key' in user['api_key']:
                key = user['api_key']['key']
                users_dict[key] = user
            
            # Also add access token as a key if available
            if 'access_token' in user:
                users_dict[user['access_token']] = user
        
        logger.info(f"Loaded {len(users_dict)} users from MongoDB")
        return users_dict
    except Exception as e:
        logger.error(f"Error loading users from MongoDB: {e}")
        traceback.print_exc()
        return {}

def save_users(users_dict: Dict[str, Any]) -> bool:
    """Save all users to MongoDB"""
    global client, db
    
    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return False
    
    try:
        # Clear existing collection data
        db[MONGODB_USER_COLLECTION].delete_many({})
        
        # Convert users dictionary to a list of documents
        users_to_insert = []
        for key, user_data in users_dict.items():
            # Make a copy to avoid modifying the original
            user_doc = user_data.copy()
            
            # Convert Decimal to Decimal128 for MongoDB storage
            user_doc = decimal_to_decimal128(user_doc)
            
            # Add the key as access_token if it's not the API key
            if 'api_key' not in user_doc or key != user_doc['api_key'].get('key'):
                user_doc['access_token'] = key
            
            users_to_insert.append(user_doc)
        
        # Insert all users
        if users_to_insert:
            db[MONGODB_USER_COLLECTION].insert_many(users_to_insert)
        
        logger.info(f"Saved {len(users_to_insert)} users to MongoDB")
        return True
    except Exception as e:
        logger.error(f"Error saving users to MongoDB: {e}")
        traceback.print_exc()
        return False

def update_user(user_key: str, user_data: Dict[str, Any]) -> bool:
    """Update a specific user in MongoDB"""
    global client, db

    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return False
    
    try:
        # Convert Decimal to Decimal128 for MongoDB storage
        user_doc = decimal_to_decimal128(user_data)
        
        # Determine if this is an API key or access token
        if 'api_key' in user_doc and user_key == user_doc['api_key'].get('key'):
            # This is an API key
            db[MONGODB_USER_COLLECTION].update_one(
                {"api_key.key": user_key},
                {"$set": user_doc},
                upsert=True
            )
        else:
            # This is an access token
            user_doc['access_token'] = user_key
            db[MONGODB_USER_COLLECTION].update_one(
                {"access_token": user_key},
                {"$set": user_doc},
                upsert=True
            )
        
        logger.info(f"Updated user with key ending in ...{user_key[-4:]}")
        return True
    except Exception as e:
        logger.error(f"Error updating user in MongoDB: {e}")
        traceback.print_exc()
        return False

def get_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Get a user by API key"""
    global client, db
    
    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return None
    
    try:
        user = db[MONGODB_USER_COLLECTION].find_one({"api_key.key": api_key})
        if user:
            user.pop('_id', None)
            return decimal128_to_decimal(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by API key: {e}")
        return None

def get_user_by_access_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Get a user by access token"""
    global client, db
    
    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return None
    
    try:
        user = db[MONGODB_USER_COLLECTION].find_one({"access_token": access_token})
        if user:
            user.pop('_id', None)
            return decimal128_to_decimal(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by access token: {e}")
        return None
