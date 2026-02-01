#!/usr/bin/env python3
"""
Models module for the Agent server.
"""

from models.enphase_models import (
    AgentMessage,
    AgentRequest,
    AgentResponse,
    EnphaseConsumptionResponse,
    EnphaseInterval,
    EnphaseProductionResponse,
    EnphaseSystemSummary,
    EnphaseTokenResponse,
    EnphaseTokenStore,
    NetEnergyData,
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    OAuthInitResponse,
    SolarConsumptionData,
    SolarProductionData,
    SystemStatusData,
    ToolCall,
)
from models.task_models import (
    ErrorResponse,
    ParsedTaskData,
    TaskCreationRequest,
    TaskCreationResponse,
)

__all__ = [
    # Enphase models
    "AgentMessage",
    "AgentRequest",
    "AgentResponse",
    "EnphaseConsumptionResponse",
    "EnphaseInterval",
    "EnphaseProductionResponse",
    "EnphaseSystemSummary",
    "EnphaseTokenResponse",
    "EnphaseTokenStore",
    "NetEnergyData",
    "OAuthCallbackRequest",
    "OAuthCallbackResponse",
    "OAuthInitResponse",
    "SolarConsumptionData",
    "SolarProductionData",
    "SystemStatusData",
    "ToolCall",
    # Task models
    "ErrorResponse",
    "ParsedTaskData",
    "TaskCreationRequest",
    "TaskCreationResponse",
]
