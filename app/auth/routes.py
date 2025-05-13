"""
Authentication routes
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from decimal import Decimal

from app.auth.models import (
    UserRegister, UserLogin, TokenResponse, 
    ApiKeyCreate, ApiKeyResponse, ApiKeyList
)
from app.utils.security import (
    hash_password, verify_password, generate_api_key, 
    generate_user_id, get_current_timestamp
)
from app.db.mongodb import (
    update_user, get_user_by_username, get_user_by_api_key, 
    get_user_by_access_token
)

# Global variables
USER_API_KEYS_STORE = {}  # In-memory store for user API keys

# Configure logging
logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme
oauth2_scheme = HTTPBearer()

async def authenticate_user_via_bearer(
    request: Request, token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> dict:
    user_key = token.credentials
    user_data = None

    # First, try to get user from MongoDB by API key
    user_data = get_user_by_api_key(user_key)
    
    # If not found by API key, try access token
    if not user_data:
        user_data = get_user_by_access_token(user_key)
        
    # If found in MongoDB, update in-memory store
    if user_data:
        USER_API_KEYS_STORE[user_key] = user_data
    
    # If not found in MongoDB, check in-memory store
    if not user_data:
        # Check if this is a direct key in our store (could be access token or API key)
        user_data = USER_API_KEYS_STORE.get(user_key)

        # If not found directly, search through all users' API key
        if not user_data:
            for key, data in USER_API_KEYS_STORE.items():
                if "api_key" in data:
                    key_info = data["api_key"]
                    if key_info.get("key") == user_key:
                        # Found a valid key, use the parent user data
                        user_data = data
                        break

    # If still not found, authentication fails
    if not user_data:
        logger.warning(f"Auth failed: Invalid key ...{user_key[-4:]}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key not valid", {"WWW-Authenticate": "Bearer"})

    # Check if API key is active
    if "api_key" in user_data and user_data["api_key"].get("key") == user_key:
        if not user_data["api_key"].get("active", True):
            logger.warning(f"Auth failed: Inactive API key ...{user_key[-4:]} for user '{user_data['username']}'")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This API key is inactive.", {"WWW-Authenticate": "Bearer"})
        
        # Update last used time for this key
        now = get_current_timestamp()
        user_data["api_key"]["last_used"] = now

    # Check if user account is active
    if not user_data.get("active", True):
        logger.warning(f"Auth failed: Inactive account for user '{user_data['username']}' (key ...{user_key[-4:]})")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This user account is inactive.", {"WWW-Authenticate": "Bearer"})

    # Check quota
    current_quota = user_data.get("quota_left")
    if current_quota is not None and current_quota <= 0:
        logger.warning(f"Quota exceeded for user '{user_data['username']}' (key ...{user_key[-4:]})")
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "API usage quota exceeded.")

    # Update in-memory store and MongoDB
    USER_API_KEYS_STORE[user_key] = user_data
    update_user(user_key, user_data)

    logger.info(f"Auth success: User '{user_data['username']}' (key ...{user_key[-4:]})")
    request.state.user_key = user_key
    request.state.user_data = user_data
    return user_data

@auth_router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegister):
    # Check if username already exists in MongoDB first
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Also check in-memory store as a fallback
    for key, data in USER_API_KEYS_STORE.items():
        if data.get("username") == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

    # Generate access token (not API key)
    access_token = generate_api_key(prefix="access_token")
    now = get_current_timestamp()

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Generate a user ID
    user_id = generate_user_id()

    # Create user entry without API key structure
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,  # Store hashed password
        "full_name": user_data.full_name,
        "active": True,
        "quota_left": 500000,  # Default quota for new users
        "request_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": Decimal("0.0"),
        "model_usage": {},
        "user_id": user_id,  # Unique user ID
        "account_created_at": now,
        "last_login": None,
        "access_token": access_token  # Store access token in user document
    }
    
    # Add to in-memory store
    USER_API_KEYS_STORE[access_token] = new_user
    
    # Save to MongoDB
    update_user(access_token, new_user)
    logger.info(f"User '{user_data.username}' registered and saved to MongoDB.")

    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        user_info={
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "quota_left": 500000,
            "active": True,
            "user_id": user_id
        }
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin):
    # Find user by username
    user_key = None
    user_info = None
    
    # First try to find user in MongoDB
    mongo_user = get_user_by_username(user_data.username)
    if mongo_user and "password_hash" in mongo_user:
        # Verify password
        if verify_password(mongo_user["password_hash"], user_data.password):
            # Get access token from user document
            if "access_token" in mongo_user:
                user_key = mongo_user["access_token"]
                user_info = mongo_user
                # Update in-memory store
                USER_API_KEYS_STORE[user_key] = mongo_user
    
    # If not found in MongoDB, check in-memory store
    if not user_key or not user_info:
        for key, data in USER_API_KEYS_STORE.items():
            if data.get("username") == user_data.username:
                # Verify password
                if "password_hash" in data and verify_password(data["password_hash"], user_data.password):
                    user_key = key
                    user_info = data
                    break

    if not user_key or not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user_info.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login time
    now = get_current_timestamp()
    user_info["last_login"] = now
    user_info.setdefault("login_count", 0)
    user_info["login_count"] += 1

    # Update last used time for the API key if it exists
    if "api_key" in user_info:
        user_info["api_key"]["last_used"] = now
    
    # Update in-memory store
    USER_API_KEYS_STORE[user_key] = user_info
    
    # Save to MongoDB
    update_user(user_key, user_info)
    logger.info(f"User '{user_data.username}' login updated in MongoDB.")

    # Return token and user info
    return TokenResponse(
        access_token=user_key,
        user_info={
            "username": user_info["username"],
            "email": user_info.get("email", ""),
            "full_name": user_info.get("full_name", ""),
            "quota_left": user_info.get("quota_left"),
            "active": user_info.get("active", True),
            "user_id": user_info.get("user_id", "")
        }
    )

@auth_router.post("/keys", response_model=ApiKeyResponse, dependencies=[Depends(authenticate_user_via_bearer)])
async def create_api_key(request: Request, key_data: ApiKeyCreate):
    """Create a new API key for the authenticated user"""
    user_data = request.state.user_data
    username = user_data["username"]
    
    # Generate a new API key
    new_api_key = generate_api_key()
    now = get_current_timestamp()

    # Store the old key if it exists
    old_key = None
    if "api_key" in user_data:
        old_key = user_data["api_key"]["key"]

    # Update the API key in the user data
    user_data["api_key"] = {
        "key": new_api_key,
        "name": key_data.name,
        "created_at": now,
        "last_used": None,
        "active": True
    }
    
    # Update in-memory store
    user_key = request.state.user_key
    USER_API_KEYS_STORE[user_key] = user_data
    
    # If this user had an old key in the store, we need to update the main store key
    if old_key and old_key in USER_API_KEYS_STORE:
        # Copy the user data to the new key
        USER_API_KEYS_STORE[new_api_key] = USER_API_KEYS_STORE[old_key].copy()
        # Update the api_key field
        USER_API_KEYS_STORE[new_api_key]["api_key"] = user_data["api_key"]
        # Delete the old key entry
        del USER_API_KEYS_STORE[old_key]
    
    # Save to MongoDB
    update_user(user_key, user_data)
    
    # If there was an old key, we need to create a new document for the new key
    if old_key:
        # Create a new document for the new API key
        new_user_data = USER_API_KEYS_STORE[new_api_key]
        update_user(new_api_key, new_user_data)
        
        # Get the old key document if it exists
        old_user = get_user_by_api_key(old_key)
        if old_user and "api_key" in old_user:
            old_user["api_key"]["active"] = False
            update_user(old_key, old_user)
    
    logger.info(f"API key for user '{username}' updated in MongoDB.")

    # Return the new key info
    return ApiKeyResponse(
        key_id="primary",
        name=key_data.name,
        key=new_api_key,  # Include the key in the response
        created_at=now,
        last_used=None,
        active=True
    )

@auth_router.get("/keys", response_model=ApiKeyList, dependencies=[Depends(authenticate_user_via_bearer)])
async def list_api_keys(request: Request):
    """List all API keys for the authenticated user"""
    user_data = request.state.user_data
    
    keys = []
    if "api_key" in user_data:
        api_key = user_data["api_key"]
        keys.append(ApiKeyResponse(
            key_id="primary",
            name=api_key.get("name", "Default API Key"),
            created_at=api_key.get("created_at", ""),
            last_used=api_key.get("last_used"),
            active=api_key.get("active", True)
        ))
    
    return ApiKeyList(keys=keys)

@auth_router.put("/keys/deactivate", dependencies=[Depends(authenticate_user_via_bearer)])
async def deactivate_api_key(request: Request):
    """Deactivate the API key"""
    user_data = request.state.user_data
    username = user_data["username"]
    
    # Check if api_key field exists
    if "api_key" not in user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Deactivate the key
    user_data["api_key"]["active"] = False
    
    # Update in-memory store
    user_key = request.state.user_key
    USER_API_KEYS_STORE[user_key] = user_data
    
    # Save to MongoDB
    update_user(user_key, user_data)
    
    # Also update the API key document if it exists
    api_key = user_data["api_key"]["key"]
    api_key_user = get_user_by_api_key(api_key)
    if api_key_user:
        api_key_user["api_key"]["active"] = False
        update_user(api_key, api_key_user)
        
    logger.info(f"API key for user '{username}' deactivated in MongoDB.")

    return {"status": "success", "message": "API key deactivated successfully"}

@auth_router.put("/keys/activate", dependencies=[Depends(authenticate_user_via_bearer)])
async def activate_api_key(request: Request):
    """Activate the API key"""
    user_data = request.state.user_data
    username = user_data["username"]
    
    # Check if api_key field exists
    if "api_key" not in user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Activate the key
    user_data["api_key"]["active"] = True
    
    # Update in-memory store
    user_key = request.state.user_key
    USER_API_KEYS_STORE[user_key] = user_data
    
    # Save to MongoDB
    update_user(user_key, user_data)
    
    # Also update the API key document if it exists
    api_key = user_data["api_key"]["key"]
    api_key_user = get_user_by_api_key(api_key)
    if api_key_user:
        api_key_user["api_key"]["active"] = True
        update_user(api_key, api_key_user)
        
    logger.info(f"API key for user '{username}' activated in MongoDB.")

    return {"status": "success", "message": "API key activated successfully"}

@auth_router.get("/profile", dependencies=[Depends(authenticate_user_via_bearer)])
async def get_user_profile(request: Request):
    """Get the authenticated user's profile"""
    user_data = request.state.user_data
    
    return {
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "full_name": user_data.get("full_name"),
        "user_id": user_data.get("user_id"),
        "quota_left": user_data.get("quota_left"),
        "request_count": user_data.get("request_count", 0),
        "total_input_tokens": user_data.get("total_input_tokens", 0),
        "total_output_tokens": user_data.get("total_output_tokens", 0),
        "account_created_at": user_data.get("account_created_at"),
        "last_login": user_data.get("last_login"),
        "active": user_data.get("active", True)
    }

@auth_router.get("/test-key", dependencies=[Depends(authenticate_user_via_bearer)])
async def test_api_key(request: Request):
    """Test if the API key is valid"""
    user_data = request.state.user_data
    
    return {
        "status": "success",
        "message": "API key is valid",
        "user_info": {
            "username": user_data.get("username"),
            "user_id": user_data.get("user_id"),
            "quota_left": user_data.get("quota_left")
        }
    }
