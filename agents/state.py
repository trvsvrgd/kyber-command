"""Pydantic-based state schema for Kyber Command graph."""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class KyberState(TypedDict):
    """Shared state for the Kyber Command multi-agent graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str | None  # Set by supervisor: "researcher" | "coder"
    pending_approval: dict | None  # Proposed action awaiting HITL approval


# Router labels used by supervisor
ROUTER_RESEARCHER: Literal["researcher"] = "researcher"
ROUTER_CODER: Literal["coder"] = "coder"
