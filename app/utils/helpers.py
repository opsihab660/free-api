"""
Helper functions for the application
"""

import json
from decimal import Decimal
from typing import Dict, Any

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal): 
            return str(obj)
        return super().default(obj)

def create_user_entry(username: str, api_key: str, active: bool = True, quota_left: int = 500000) -> Dict[str, Any]:
    """Create a basic user entry with API key structure
    
    Args:
        username: Username for the user
        api_key: API key for the user
        active: Whether the user is active (default: True)
        quota_left: Quota left for the user (default: 500000)
        
    Returns:
        A dictionary with user data
    """
    from app.utils.security import get_current_timestamp, generate_user_id
    
    current_time = get_current_timestamp()
    user_id = generate_user_id()

    return {
        "username": username,
        "active": active,
        "quota_left": quota_left,
        "user_id": user_id,
        "api_key": {
            "key": api_key,
            "name": "Default API Key",
            "created_at": current_time,
            "last_used": None,
            "active": active
        },
        "account_created_at": current_time,
        "request_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": Decimal("0.0"),
        "model_usage": {}
    }
