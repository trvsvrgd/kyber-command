"""Tests for graph routing logic."""

from langchain_core.messages import AIMessage
from langgraph.graph import END

from agents.state import ROUTER_CODER, ROUTER_RESEARCHER
from graph_engine import _route_after_supervisor, _should_continue_coder


class TestRouteAfterSupervisor:
    """Tests for _route_after_supervisor."""

    def test_routes_to_coder_when_next_agent_coder(self) -> None:
        state = {"next_agent": ROUTER_CODER, "messages": []}
        assert _route_after_supervisor(state) == ROUTER_CODER

    def test_routes_to_researcher_when_next_agent_researcher(self) -> None:
        state = {"next_agent": ROUTER_RESEARCHER, "messages": []}
        assert _route_after_supervisor(state) == ROUTER_RESEARCHER

    def test_defaults_to_researcher_when_next_agent_missing(self) -> None:
        state = {}
        assert _route_after_supervisor(state) == ROUTER_RESEARCHER

    def test_defaults_to_researcher_when_next_agent_none(self) -> None:
        state = {"next_agent": None}
        assert _route_after_supervisor(state) == ROUTER_RESEARCHER


class TestShouldContinueCoder:
    """Tests for _should_continue_coder."""

    def test_returns_coder_tools_when_last_message_has_tool_calls(self) -> None:
        msg = AIMessage(content="", tool_calls=[{"id": "1", "name": "read_file", "args": {"path": "x"}}])
        state = {"messages": [msg]}
        assert _should_continue_coder(state) == "coder_tools"

    def test_returns_end_when_last_message_no_tool_calls(self) -> None:
        msg = AIMessage(content="done")
        state = {"messages": [msg]}
        assert _should_continue_coder(state) == END

    def test_returns_end_when_empty_messages(self) -> None:
        state = {"messages": []}
        assert _should_continue_coder(state) == END
