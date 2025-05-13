"""
Main application entry point
"""

import logging
import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from app.config.settings import LOCAL_SERVER_PORT, YOUR_BACKEND_API_KEY, BACKEND_API_BASE_URL
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection, load_all_users, save_users
from app.auth.routes import auth_router, USER_API_KEYS_STORE
from app.api.routes import api_router, set_backend_client
from app.utils.helpers import CustomJSONEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the FastAPI application
    """
    # Startup logic
    global backend_openai_client

    # Initialize MongoDB connection
    mongodb_connected = connect_to_mongodb()
    if mongodb_connected:
        logger.info("MongoDB connection established successfully.")
        # Load user data from MongoDB
        mongo_users = load_all_users()
        if mongo_users:
            # Only update the in-memory store if it's empty or has fewer users
            # This prevents overwriting MongoDB data when the service restarts
            if not USER_API_KEYS_STORE or len(mongo_users) > len(USER_API_KEYS_STORE):
                USER_API_KEYS_STORE.update(mongo_users)
                logger.info(f"Loaded {len(mongo_users)} users from MongoDB into in-memory store.")
            else:
                logger.info(f"In-memory store already has {len(USER_API_KEYS_STORE)} users. Not overwriting with {len(mongo_users)} from MongoDB.")
    else:
        logger.error("MongoDB connection failed. Application will not be able to store data.")

    # Initialize OpenAI client
    if YOUR_BACKEND_API_KEY:
        backend_client = AsyncOpenAI(api_key=YOUR_BACKEND_API_KEY, base_url=BACKEND_API_BASE_URL)
        # Set the backend client in the API module
        set_backend_client(backend_client)
        logger.info(f"Startup: OpenAI backend client configured for {BACKEND_API_BASE_URL}.")
    else:
        logger.error("FATAL: MY_BACKEND_API_KEY not set. Backend client NOT initialized.")

    yield  # This is where FastAPI serves requests

    # Shutdown logic
    if mongodb_connected:
        # First check if we have users in the in-memory store
        if USER_API_KEYS_STORE:
            # Get current count of users in MongoDB
            mongo_users = load_all_users()
            mongo_user_count = len(mongo_users) if mongo_users else 0

            # Only save if we have a reasonable number of users in memory
            # This prevents accidentally wiping out the database if the in-memory store is empty
            if len(USER_API_KEYS_STORE) >= mongo_user_count:
                # Save user data to MongoDB
                save_users(USER_API_KEYS_STORE)
                logger.info(f"User stats saved to MongoDB: {len(USER_API_KEYS_STORE)} users.")
            else:
                logger.warning(f"Not saving in-memory store to MongoDB: In-memory has {len(USER_API_KEYS_STORE)} users, MongoDB has {mongo_user_count}.")
        else:
            logger.warning("In-memory store is empty. Not saving to MongoDB to prevent data loss.")

        # Close MongoDB connection
        close_mongodb_connection()
    else:
        logger.error("MongoDB connection not available. User stats not saved.")

# Create FastAPI app
app = FastAPI(
    title="API Service",
    description="API Service with MongoDB integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth_router)
app.include_router(api_router)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the API Service",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/admin/stats", tags=["Admin"], summary="View current user statistics")
async def view_stats():
    """View current user statistics"""
    # If MongoDB is available, refresh the in-memory store first
    mongo_users = load_all_users()
    if mongo_users:
        # Only update the in-memory store if MongoDB has more users
        # This prevents accidentally losing data when the service restarts
        if len(mongo_users) > len(USER_API_KEYS_STORE):
            USER_API_KEYS_STORE.update(mongo_users)
            logger.info(f"Refreshed in-memory store with {len(mongo_users)} users from MongoDB.")
        else:
            logger.info(f"In-memory store has {len(USER_API_KEYS_STORE)} users, MongoDB has {len(mongo_users)}. Not updating in-memory store.")

    # Use dumps with custom encoder for top-level USER_API_KEYS_STORE
    # then parse back to ensure JSONResponse gets a structure it can handle
    # This is a bit of a workaround for nested Decimals with JSONResponse
    json_str = json.dumps(USER_API_KEYS_STORE, cls=CustomJSONEncoder)
    return JSONResponse(content=json.loads(json_str))

if __name__ == "__main__":
    import uvicorn
    # For local development, use 127.0.0.1
    # For production on Render, the app will be available at the Render URL
    port = int(os.environ.get("PORT", LOCAL_SERVER_PORT))
    host = "0.0.0.0"  # Listen on all interfaces (local development)
    local_url = f"http://127.0.0.1:{port}"

    print(f"সার্ভার চালু হচ্ছে {local_url} এ (local development)")
    print(f"OpenAI SDK Base URL: '{local_url}/v1/api' (local development)")

    # MongoDB connection info
    from app.config.settings import MONGODB_URI
    print(f"MongoDB URI: '{MONGODB_URI}'")

    print("API Keys (Authorization: Bearer <key>):")
    for key, data in USER_API_KEYS_STORE.items():
        print(f"  - Key: {key} (User: {data['username']}, Active: {data.get('active', True)}, Quota: {data.get('quota_left', 'N/A')})")

    if not YOUR_BACKEND_API_KEY:
        print("WARNING: MY_BACKEND_API_KEY is not set. Backend calls will fail.")

    # Use the same port and host configuration as defined above
    uvicorn.run(app, host=host, port=port)
