"""
Vercel-specific entry point for the API Service
"""

import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

import sys
import os
# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import YOUR_BACKEND_API_KEY, BACKEND_API_BASE_URL
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
            USER_API_KEYS_STORE.update(mongo_users)
            logger.info(f"Loaded {len(USER_API_KEYS_STORE)} users from MongoDB.")
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
        # Save user data to MongoDB
        save_users(USER_API_KEYS_STORE)
        logger.info("User stats saved to MongoDB.")
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
        # Update the in-memory store with the latest data from MongoDB
        USER_API_KEYS_STORE.update(mongo_users)
        logger.info(f"Refreshed in-memory store with {len(mongo_users)} users from MongoDB.")

    # Use dumps with custom encoder for top-level USER_API_KEYS_STORE
    # then parse back to ensure JSONResponse gets a structure it can handle
    # This is a bit of a workaround for nested Decimals with JSONResponse
    json_str = json.dumps(USER_API_KEYS_STORE, cls=CustomJSONEncoder)
    return JSONResponse(content=json.loads(json_str))
