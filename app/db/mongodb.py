"""
MongoDB client module for handling database operations.
This module provides functions to connect to MongoDB and perform CRUD operations.
"""

import logging
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.database import Database
from decimal import Decimal
from bson import Decimal128
from datetime import datetime

from app.config.settings import MONGODB_URI, MONGODB_DB_NAME, MONGODB_USER_COLLECTION

# Configure logging
logger = logging.getLogger(__name__)

# Global MongoDB client
client: Optional[MongoClient] = None
db: Optional[Database] = None

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

    try:
        # Create MongoDB client
        client = MongoClient(MONGODB_URI)

        # Check connection
        client.admin.command('ping')

        # Get database and collections
        db = client[MONGODB_DB_NAME]

        # Create indexes for faster lookups
        db[MONGODB_USER_COLLECTION].create_index("username", unique=True)
        db[MONGODB_USER_COLLECTION].create_index("api_key.key", unique=True, sparse=True)
        db[MONGODB_USER_COLLECTION].create_index("user_id", unique=True)

        logger.info(f"Connected to MongoDB at {MONGODB_URI}, database: {MONGODB_DB_NAME}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
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
        return {}

def save_users(users_dict: Dict[str, Any]) -> bool:
    """Save all users to MongoDB"""
    global client, db

    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return False

    try:
        # Get existing users from MongoDB to avoid deleting them
        existing_users = {}
        existing_usernames = set()
        existing_api_keys = set()
        existing_access_tokens = set()

        users_cursor = db[MONGODB_USER_COLLECTION].find({})
        for user in users_cursor:
            user.pop('_id', None)

            # Track existing usernames, API keys, and access tokens
            if 'username' in user:
                existing_usernames.add(user['username'])

            if 'api_key' in user and 'key' in user['api_key']:
                existing_api_keys.add(user['api_key']['key'])

            if 'access_token' in user:
                existing_access_tokens.add(user['access_token'])

        # Process in-memory users
        update_count = 0
        insert_count = 0

        for key, user_data in users_dict.items():
            # Make a copy to avoid modifying the original
            user_doc = user_data.copy()

            # Convert Decimal to Decimal128 for MongoDB storage
            user_doc = decimal_to_decimal128(user_doc)

            # Add the key as access_token if it's not the API key
            if 'api_key' not in user_doc or key != user_doc['api_key'].get('key'):
                user_doc['access_token'] = key

            # Check if this is an existing user
            username = user_doc.get('username')
            api_key = user_doc.get('api_key', {}).get('key')
            access_token = user_doc.get('access_token')

            # Determine if we should update or insert
            should_update = False
            update_query = {}

            if username and username in existing_usernames:
                update_query = {"username": username}
                should_update = True
            elif api_key and api_key in existing_api_keys:
                update_query = {"api_key.key": api_key}
                should_update = True
            elif access_token and access_token in existing_access_tokens:
                update_query = {"access_token": access_token}
                should_update = True

            if should_update:
                # Update existing user
                db[MONGODB_USER_COLLECTION].update_one(
                    update_query,
                    {"$set": user_doc}
                )
                update_count += 1
            else:
                # Insert new user
                db[MONGODB_USER_COLLECTION].insert_one(user_doc)
                insert_count += 1

        logger.info(f"Saved users to MongoDB: {update_count} updated, {insert_count} inserted")
        return True
    except Exception as e:
        logger.error(f"Error saving users to MongoDB: {e}")
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
        return False

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get a user by username"""
    global client, db

    if client is None or db is None:
        logger.error("MongoDB connection not established")
        return None

    try:
        user = db[MONGODB_USER_COLLECTION].find_one({"username": username})
        if user:
            user.pop('_id', None)
            return decimal128_to_decimal(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None

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
