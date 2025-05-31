"""
Agent state models for the Vibe Mapping Agent.

This module contains Pydantic models for representing the state of the agent
during conversations and processing.
"""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Pydantic model for the agent state.

    This model defines the structure and validation for the agent's state
    in a LangGraph conversation.
    """

    messages: List[Any] = Field(
        default_factory=list,
        description="List of conversation messages",
    )
    tools: List[Any] = Field(
        default_factory=list,
        description="List of available tools",
    )
    last_tool_outputs: List[Any] = Field(
        default_factory=list,
        description="Outputs from the last tool executions",
    )
    current_tool: Optional[Any] = Field(
        default=None,
        description="Currently executing tool, if any",
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
    streaming: bool = Field(default=False, description="Whether streaming mode is enabled")
    streaming_messages: Optional[List[Any]] = Field(
        default=None,
        description="Messages formatted for streaming response",
    )
    needs_streaming_response: bool = Field(
        default=False,
        description="Whether the agent needs to stream a response",
    )