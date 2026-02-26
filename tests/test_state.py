"""Tests for agents.state."""

from agents.state import ROUTER_CODER, ROUTER_RESEARCHER


def test_router_constants() -> None:
    """Router literals are set correctly."""
    assert ROUTER_RESEARCHER == "researcher"
    assert ROUTER_CODER == "coder"
