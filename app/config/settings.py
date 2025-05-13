"""
Application settings and configuration
"""

import os
from decimal import Decimal, getcontext

# Import environment variables loader
from app.config.env import load_env_file

# Ensure environment variables are loaded
load_env_file()

# Set high precision for Decimal
getcontext().prec = 28

# Server settings
LOCAL_SERVER_PORT = int(os.environ.get("LOCAL_SERVER_PORT", 8002))

# API settings
BACKEND_API_BASE_URL = os.environ.get("BACKEND_API_BASE_URL", "https://api.devsdocode.com/v1")
YOUR_BACKEND_API_KEY = os.environ.get("MY_BACKEND_API_KEY", "ddc-temp-free-e3b73cd814cc4f3ea79b5d4437912663")
PROVIDER_PREFIX = "provider-4/"

# MongoDB settings
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://yoosihab:opsihab660@cluster0.cexbyfs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "api_service_db")
MONGODB_USER_COLLECTION = "users"

# Model costs configuration
MODEL_COSTS = {
    "provider-4/gpt-4.1": {"input_cost_per_token": Decimal("0.00000200"), "output_cost_per_token": Decimal("0.00000800")},
    "provider-4/gpt-4.1-mini": {"input_cost_per_token": Decimal("0.00000040"), "output_cost_per_token": Decimal("0.00000160")},
    "provider-4/gpt-4.1-nano": {"input_cost_per_token": Decimal("0.00000010"), "output_cost_per_token": Decimal("0.00000040")},
    "provider-4/gpt-4o": {"input_cost_per_token": Decimal("0.00000500"), "output_cost_per_token": Decimal("0.00001500")},
    "provider-4/gpt-4o-mini": {"input_cost_per_token": Decimal("0.00000015"), "output_cost_per_token": Decimal("0.00000060")},
    "provider-4/o3-mini": {"input_cost_per_token": Decimal("0"), "output_cost_per_token": Decimal("0"), "comment": "Pricing N/A"},
    "provider-4/deepseek-r1": {"input_cost_per_token": Decimal("0.00000800"), "output_cost_per_token": Decimal("0.00000800")},
    "provider-4/deepseek-v3": {"input_cost_per_token": Decimal("0"), "output_cost_per_token": Decimal("0"), "comment": "Pricing varies"},
    "provider-4/llama-4-scout": {"input_cost_per_token": Decimal("0.00000011"), "output_cost_per_token": Decimal("0.00000034")},
    "provider-4/llama-4-maverick": {"input_cost_per_token": Decimal("0.00000050"), "output_cost_per_token": Decimal("0.00000077")},
    "provider-4/mistral-large-latest": {"input_cost_per_token": Decimal("0.00000800"), "output_cost_per_token": Decimal("0.00002400")},
    "provider-4/mistral-small": {"input_cost_per_token": Decimal("0.00000200"), "output_cost_per_token": Decimal("0.00000600")},
    "provider-4/gemini-2.5-flash-preview-04-17": {"input_cost_per_token": Decimal("0.00000015"), "output_cost_per_token": Decimal("0.00000060")},
    "provider-4/gemini-2.5-pro-exp-03-25": {"input_cost_per_token": Decimal("0.00000125"), "output_cost_per_token": Decimal("0.00001000")},
    "gpt-3.5-turbo": {"input_cost_per_token": Decimal("0.0000005"), "output_cost_per_token": Decimal("0.0000015")},
    "default_model_for_costing": {"input_cost_per_token": Decimal("0"), "output_cost_per_token": Decimal("0"), "comment": "Default if model not found"}
}

# Model name mapping
MODEL_NAME_MAPPING = {name: f"{PROVIDER_PREFIX}{name}" for name in [
    "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o", "gpt-4o-mini", "o3-mini",
    "deepseek-r1", "deepseek-v3", "llama-4-scout", "llama-4-maverick",
    "mistral-large-latest", "mistral-small",
    "gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-exp-03-25"
]}
