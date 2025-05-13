"""
Vercel-specific entry point for the API Service
"""

import logging
import json
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

import sys
import os
# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try importing the required modules with error handling
try:
    # Import settings directly from environment variables
    import os
    YOUR_BACKEND_API_KEY = os.environ.get("MY_BACKEND_API_KEY", "")
    BACKEND_API_BASE_URL = os.environ.get("BACKEND_API_BASE_URL", "https://api.devsdocode.com/v1")

    # Import MongoDB functions from our Vercel-specific module
    from api.mongodb_vercel import connect_to_mongodb, close_mongodb_connection, load_all_users, save_users, get_user_by_api_key, get_user_by_access_token, update_user

    # Import other modules from the app
    from app.auth.routes import auth_router, USER_API_KEYS_STORE
    from app.api.routes import api_router, set_backend_client
    from app.utils.helpers import CustomJSONEncoder

    # Monkey patch the MongoDB functions in app.db.mongodb
    import app.db.mongodb
    app.db.mongodb.connect_to_mongodb = connect_to_mongodb
    app.db.mongodb.close_mongodb_connection = close_mongodb_connection
    app.db.mongodb.load_all_users = load_all_users
    app.db.mongodb.save_users = save_users
    app.db.mongodb.get_user_by_api_key = get_user_by_api_key
    app.db.mongodb.get_user_by_access_token = get_user_by_access_token
    app.db.mongodb.update_user = update_user

except Exception as e:
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    # Re-raise to see in Vercel logs
    raise

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add debug endpoint
@app.get("/debug", tags=["Debug"])
async def debug_info():
    """Debug endpoint to check environment and imports"""
    import sys
    import os

    debug_info = {
        "python_version": sys.version,
        "sys_path": sys.path,
        "environment_variables": {k: v for k, v in os.environ.items() if not k.startswith("AWS_") and not k.lower().startswith("secret")},
        "current_directory": os.getcwd(),
        "directory_contents": os.listdir(os.getcwd()) if os.path.exists(os.getcwd()) else "Cannot list directory",
        "app_directory": os.path.dirname(os.path.abspath(__file__)),
        "mongodb_uri_configured": bool(os.environ.get("MONGODB_URI")),
        "backend_api_key_configured": bool(os.environ.get("MY_BACKEND_API_KEY")),
    }

    return JSONResponse(content=debug_info)

# Include routers
try:
    app.include_router(auth_router)
    app.include_router(api_router)
except Exception as e:
    logger.error(f"Error including routers: {e}")
    traceback.print_exc()

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
