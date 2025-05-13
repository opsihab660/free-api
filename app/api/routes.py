"""
API routes for OpenAI-compatible endpoints
"""

import logging
import json
from decimal import Decimal
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from openai import AsyncOpenAI, APIError, AuthenticationError as OpenAIAuthError

from app.auth.routes import authenticate_user_via_bearer, USER_API_KEYS_STORE
from app.config.settings import (
    YOUR_BACKEND_API_KEY, BACKEND_API_BASE_URL,
    MODEL_NAME_MAPPING, MODEL_COSTS
)
from app.db.mongodb import update_user
from app.utils.helpers import CustomJSONEncoder

# Configure logging
logger = logging.getLogger(__name__)

# Create router
api_router = APIRouter(prefix="/v1/api", tags=["API"])

# Global OpenAI client
backend_openai_client = None

# This will be set in main.py during startup
def set_backend_client(client):
    global backend_openai_client
    backend_openai_client = client

async def proxy_openai_chat_completions(request: Request):
    """Proxy OpenAI chat completions API"""
    if not backend_openai_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend API client not initialized"
        )

    # Get user data from request state
    user_data = request.state.user_data
    username = user_data.get("username", "unknown")
    user_key = request.state.user_key

    # Parse request body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body"
        )

    # Get model name from request
    model_name = body.get("model", "gpt-3.5-turbo")

    # Map model name if needed
    original_model_name_for_stats = model_name
    if model_name in MODEL_NAME_MAPPING:
        model_name_from_payload = MODEL_NAME_MAPPING[model_name]
        body["model"] = model_name_from_payload
    else:
        model_name_from_payload = model_name

    # Check if streaming is requested
    stream = body.get("stream", False)

    try:
        if stream:
            # Handle streaming response
            async def generate():
                async for chunk in backend_openai_client.chat.completions.create(**body, stream=True):
                    yield f"data: {json.dumps(chunk.model_dump())}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Handle non-streaming response
            response = await backend_openai_client.chat.completions.create(**body)
            response_dict = response.model_dump()

            # Calculate token usage and cost
            usage = response_dict.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # Get model costs
            model_costs = MODEL_COSTS.get(original_model_name_for_stats) or MODEL_COSTS.get(model_name_from_payload) or MODEL_COSTS["default_model_for_costing"]
            input_cost_per_token = model_costs.get("input_cost_per_token", Decimal("0"))
            output_cost_per_token = model_costs.get("output_cost_per_token", Decimal("0"))

            # Calculate cost
            input_cost = Decimal(input_tokens) * input_cost_per_token
            output_cost = Decimal(output_tokens) * output_cost_per_token
            cost_this_req = input_cost + output_cost

            # Update user stats
            user_data["request_count"] = user_data.get("request_count", 0) + 1
            user_data["total_input_tokens"] = user_data.get("total_input_tokens", 0) + input_tokens
            user_data["total_output_tokens"] = user_data.get("total_output_tokens", 0) + output_tokens

            # Initialize total_cost if not present
            if "total_cost" not in user_data:
                user_data["total_cost"] = Decimal("0")

            # Update total cost
            user_data["total_cost"] += cost_this_req

            # Update quota
            if "quota_left" in user_data:
                user_data["quota_left"] -= (input_tokens + output_tokens)
                if user_data["quota_left"] < 0:
                    user_data["quota_left"] = 0

            # Update model-specific stats
            if "model_usage" not in user_data:
                user_data["model_usage"] = {}

            if original_model_name_for_stats not in user_data["model_usage"]:
                user_data["model_usage"][original_model_name_for_stats] = {
                    "request_count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": Decimal("0")
                }

            model_specific_stats = user_data["model_usage"][original_model_name_for_stats]
            model_specific_stats["request_count"] += 1
            model_specific_stats["input_tokens"] += input_tokens
            model_specific_stats["output_tokens"] += output_tokens
            model_specific_stats["cost"] += cost_this_req

            # Log usage
            logger.info(
                f"User '{username}' | Model '{original_model_name_for_stats}' (Backend: '{model_name_from_payload}') | "
                f"Req# {user_data['request_count']}(M:{model_specific_stats['request_count']}) | "
                f"InTok {user_data['total_input_tokens']}(+{input_tokens}) | "
                f"OutTok {user_data['total_output_tokens']}(+{output_tokens}) | "
                f"Cost ${user_data['total_cost']:.10f}(+${cost_this_req:.10f}) | "
                f"MCost ${model_specific_stats['cost']:.10f} | "
                f"Quota {user_data['quota_left']}"
            )

            # Update in-memory store
            USER_API_KEYS_STORE[user_key] = user_data

            # Save to MongoDB
            update_user(user_key, user_data)
            logger.info(f"User stats for '{username}' updated in MongoDB.")

            # Add user ID to response
            if "id" in response_dict:
                response_dict["id"] = user_data.get("user_id", response_dict["id"])

            # Add username to response
            response_dict["username"] = username

            return JSONResponse(content=response_dict)

    except OpenAIAuthError as e:
        logger.error(f"OpenAI authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Backend API authentication error"
        )
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error proxying request: {str(e)}"
        )

# Register routes
api_router.add_api_route("/chat/completions", proxy_openai_chat_completions, methods=["POST"], dependencies=[Depends(authenticate_user_via_bearer)])
