#!/usr/bin/env python3
"""
Unified Agent route handler.

This endpoint provides a conversational agent that can:
- Query solar production/consumption data via Enphase tools
- Create tasks via task creation tools
- Chain actions together (e.g., "my production is low, create a task to check panels")
"""

import json
import logging
from typing import Any, Dict, List, Optional

import openai
from fastapi import APIRouter, Depends, HTTPException
from models.enphase_models import (
    AgentRequest,
    AgentResponse,
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    OAuthInitResponse,
    ToolCall,
)
from services.enphase import EnphaseService
from services.task_creation import TaskCreationService
from tools.registry import execute_tool, get_all_tools
from utils.auth import verify_bearer_token
from utils.config import config

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["agent"])

# Global Enphase service instance (lazy initialization)
_enphase_service: Optional[EnphaseService] = None


def get_enphase_service() -> Optional[EnphaseService]:
    """Get or initialize the Enphase service."""
    global _enphase_service

    if _enphase_service is None and config.is_enphase_configured():
        try:
            _enphase_service = EnphaseService(
                client_id=config.ENPHASE_CLIENT_ID,
                client_secret=config.ENPHASE_CLIENT_SECRET,
                api_key=config.ENPHASE_API_KEY,
                system_id=config.ENPHASE_SYSTEM_ID,
                access_token=config.ENPHASE_ACCESS_TOKEN,
                refresh_token=config.ENPHASE_REFRESH_TOKEN,
                redirect_uri=config.ENPHASE_REDIRECT_URI,
                timezone=config.ENPHASE_TIMEZONE,
            )
            logger.info("Enphase service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Enphase service: {e}")
            return None

    return _enphase_service


def get_openai_client() -> openai.OpenAI:
    """Get OpenAI client."""
    return openai.OpenAI(api_key=config.OPENAI_API_KEY)


@router.post("/agent", response_model=AgentResponse)
async def agent_chat(
    request: AgentRequest,
    authenticated: bool = Depends(verify_bearer_token),
) -> AgentResponse:
    """
    Unified agent endpoint for conversational AI with tool access.

    This endpoint:
    1. Receives a user message
    2. Uses OpenAI with function calling to determine which tools to use
    3. Executes the appropriate tools (Enphase solar, task creation)
    4. Returns a natural language response with structured data

    Args:
        request: AgentRequest with user message and options

    Returns:
        AgentResponse with message, tool calls, and structured data
    """
    try:
        logger.info(f"🤖 Agent received message: {request.message[:100]}...")

        # Initialize services
        enphase_service = get_enphase_service() if request.include_solar_context else None
        task_service = None

        # Build available tools based on configuration and request
        available_tools = get_all_tools(
            include_enphase=request.include_solar_context and enphase_service is not None,
            include_tasks=request.include_task_context,
        )

        # Check if we have any tools available
        if not available_tools:
            logger.warning("No tools available for agent")

        # Build messages for OpenAI
        messages = _build_messages(request)

        # Get OpenAI client
        client = get_openai_client()

        # Make initial request with tools
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=available_tools if available_tools else None,
            tool_choice="auto" if available_tools else None,
            temperature=0.7,
            max_tokens=1000,
        )

        # Process response
        assistant_message = response.choices[0].message
        tool_calls_made: List[ToolCall] = []
        solar_data: Optional[Dict[str, Any]] = None
        task_data: Optional[Dict[str, Any]] = None

        # Check if the model wants to call tools
        if assistant_message.tool_calls:
            logger.info(f"🔧 Agent calling {len(assistant_message.tool_calls)} tools")

            # Execute each tool call
            tool_results = []
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                logger.info(f"  - Executing tool: {tool_name}")

                # Initialize task service if needed
                if tool_name == "create_task" and task_service is None:
                    task_service = TaskCreationService(dry_run=False)

                # Execute the tool
                result = execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    enphase_service=enphase_service,
                    task_service=task_service,
                )

                # Record the tool call
                tool_calls_made.append(
                    ToolCall(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result,
                    )
                )

                # Categorize results
                if tool_name in ["get_solar_production", "get_energy_consumption", 
                                 "get_net_energy_usage", "get_system_status"]:
                    solar_data = result.get("data")
                elif tool_name == "create_task":
                    task_data = result.get("data")

                # Add tool result for follow-up
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": json.dumps(result),
                })

            # Get final response from OpenAI with tool results
            messages.append(assistant_message)
            messages.extend(tool_results)

            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )

            final_message = final_response.choices[0].message.content or ""
        else:
            # No tool calls, just return the response
            final_message = assistant_message.content or ""

        logger.info("✅ Agent response generated successfully")

        return AgentResponse(
            success=True,
            message=final_message,
            tool_calls=tool_calls_made,
            solar_data=solar_data,
            task_data=task_data,
        )

    except Exception as e:
        logger.error(f"❌ Agent error: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            message=f"I encountered an error: {str(e)}",
            tool_calls=[],
        )


def _build_messages(request: AgentRequest) -> List[Dict[str, str]]:
    """Build the messages list for OpenAI."""
    messages = [
        {
            "role": "system",
            "content": _get_system_prompt(request),
        }
    ]

    # Add conversation history if provided
    if request.conversation_history:
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

    # Add the current user message
    messages.append({
        "role": "user",
        "content": request.message,
    })

    return messages


def _get_system_prompt(request: AgentRequest) -> str:
    """Generate the system prompt based on available capabilities."""
    capabilities = []

    if request.include_solar_context:
        capabilities.append(
            "- Query solar panel production data (how much energy was generated)"
            "\n- Query home energy consumption data (how much energy was used)"
            "\n- Calculate net energy usage (production vs consumption, grid import/export)"
            "\n- Get current system status (real-time production, system health)"
        )

    if request.include_task_context:
        capabilities.append(
            "- Create tasks in Notion with AI-powered parsing"
            "\n- Set priorities, due dates, and workspaces for tasks"
        )

    capabilities_text = "\n".join(capabilities) if capabilities else "No tools currently available."

    return f"""You are a helpful personal assistant with access to the following capabilities:

{capabilities_text}

Guidelines:
- Be conversational and friendly
- When providing energy data, include helpful context (comparisons, trends)
- If the user mentions a problem (e.g., low production), offer to create a task
- Use the appropriate tools to fulfill user requests
- Format numbers nicely (e.g., "42.5 kWh" not "42.50000 kWh")
- When creating tasks, include relevant context from the conversation

Current context:
- Today's date: Use ISO format for any date-related queries
- Timezone: America/Chicago (Central Time)
"""


# =============================================================================
# OAuth Endpoints for Enphase Authorization
# =============================================================================


@router.get("/enphase/oauth/init", response_model=OAuthInitResponse)
async def init_enphase_oauth(
    authenticated: bool = Depends(verify_bearer_token),
) -> OAuthInitResponse:
    """
    Initialize Enphase OAuth flow.

    Returns the authorization URL to redirect the user for consent.
    """
    if not config.is_enphase_configured():
        raise HTTPException(
            status_code=503,
            detail="Enphase API not configured. Set ENPHASE_CLIENT_ID, ENPHASE_CLIENT_SECRET, and ENPHASE_API_KEY.",
        )

    try:
        service = EnphaseService()
        auth_url, state = service.get_authorization_url()

        return OAuthInitResponse(
            auth_url=auth_url,
            state=state,
        )
    except Exception as e:
        logger.error(f"Failed to initialize OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enphase/oauth/callback", response_model=OAuthCallbackResponse)
async def enphase_oauth_callback(
    request: OAuthCallbackRequest,
    authenticated: bool = Depends(verify_bearer_token),
) -> OAuthCallbackResponse:
    """
    Handle Enphase OAuth callback.

    Exchange the authorization code for access and refresh tokens.
    """
    if not config.is_enphase_configured():
        raise HTTPException(
            status_code=503,
            detail="Enphase API not configured.",
        )

    try:
        service = EnphaseService()
        token_response = service.exchange_code_for_tokens(request.code)

        # Update the global service with new tokens
        global _enphase_service
        _enphase_service = service

        return OAuthCallbackResponse(
            success=True,
            message="Successfully authenticated with Enphase. Tokens have been saved.",
            access_token=token_response.access_token[:20] + "...",  # Partial for security
            refresh_token=token_response.refresh_token[:20] + "...",
            expires_in=token_response.expires_in,
        )
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        return OAuthCallbackResponse(
            success=False,
            message=f"OAuth failed: {str(e)}",
        )


@router.get("/enphase/status")
async def get_enphase_status(
    authenticated: bool = Depends(verify_bearer_token),
) -> Dict[str, Any]:
    """
    Get Enphase integration status.

    Returns configuration status and whether tokens are available.
    """
    return {
        "configured": config.is_enphase_configured(),
        "has_tokens": config.has_enphase_tokens(),
        "system_id": config.ENPHASE_SYSTEM_ID or None,
        "service_initialized": _enphase_service is not None,
    }


# =============================================================================
# Direct Data Endpoints (for testing/debugging)
# =============================================================================


@router.get("/enphase/production")
async def get_production_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    authenticated: bool = Depends(verify_bearer_token),
) -> Dict[str, Any]:
    """
    Get solar production data directly.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    service = get_enphase_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enphase service not available. Check configuration and tokens.",
        )

    try:
        result = service.get_production(start_date=start_date, end_date=end_date)
        return {"success": True, "data": result.model_dump()}
    except Exception as e:
        logger.error(f"Failed to get production data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enphase/consumption")
async def get_consumption_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    authenticated: bool = Depends(verify_bearer_token),
) -> Dict[str, Any]:
    """
    Get energy consumption data directly.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    service = get_enphase_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enphase service not available. Check configuration and tokens.",
        )

    try:
        result = service.get_consumption(start_date=start_date, end_date=end_date)
        return {"success": True, "data": result.model_dump()}
    except Exception as e:
        logger.error(f"Failed to get consumption data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enphase/net")
async def get_net_energy_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    authenticated: bool = Depends(verify_bearer_token),
) -> Dict[str, Any]:
    """
    Get net energy usage data directly.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    service = get_enphase_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enphase service not available. Check configuration and tokens.",
        )

    try:
        result = service.get_net_energy(start_date=start_date, end_date=end_date)
        return {"success": True, "data": result.model_dump()}
    except Exception as e:
        logger.error(f"Failed to get net energy data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enphase/system")
async def get_system_status_data(
    authenticated: bool = Depends(verify_bearer_token),
) -> Dict[str, Any]:
    """Get current system status directly."""
    service = get_enphase_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Enphase service not available. Check configuration and tokens.",
        )

    try:
        result = service.get_system_status()
        return {"success": True, "data": result.model_dump()}
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
