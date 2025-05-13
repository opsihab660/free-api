"""
Security utilities for authentication and authorization
"""

import os
import secrets
import string
import hashlib
import base64
import logging
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    salt = os.urandom(32)  # 32 bytes salt
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + pwdhash).decode('utf-8')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    try:
        decoded = base64.b64decode(stored_password.encode('utf-8'))
        salt = decoded[:32]  # 32 bytes salt
        stored_hash = decoded[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return pwdhash == stored_hash
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def generate_api_key(prefix: str = "user_key") -> str:
    """Generate a unique API key for a user
    
    Args:
        prefix: Optional prefix for the key (default: "user_key")
    
    Returns:
        A unique API key string
    """
    # Format: {prefix}_{random_string}
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(24))
    return f"{prefix}_{random_part}"

def generate_user_id() -> str:
    """Generate a unique user ID"""
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format with timezone"""
    return datetime.now(timezone.utc).isoformat()
