"""Kyber Command - LangGraph orchestration engine with AsyncSqliteSaver."""

import asyncio
from pathlib import Path

import yaml
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agents.coder import CODER_TOOLS, create_coder_llm, create_coder_node
from agents.researcher import create_researcher_llm, researcher_node
from agents.state import KyberState, ROUTER_CODER, ROUTER_RESEARCHER
from agents.supervisor import create_supervisor_llm, supervisor_node

# Global checkpointer context manager to keep connection alive
_checkpointer_cm = None
_checkpointer = None


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _route_after_supervisor(state: KyberState) -> str:
    """Route to researcher or coder based on supervisor's decision."""
    next_agent = state.get("next_agent") or ROUTER_RESEARCHER
    return next_agent


def _should_continue_coder(state: KyberState) -> str:
    """If last AIMessage has tool_calls, go to coder_tools; else END."""
    messages = state.get("messages", [])
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage) and last.tool_calls:
        return "coder_tools"
    return END


async def build_graph(config: dict | None = None):
    """Build and compile the Kyber Command LangGraph."""
    config = config or load_config()

    ollama = config.get("ollama", {})
    base_url = ollama.get("base_url", "http://localhost:11434")
    temperature = ollama.get("temperature", 0.7)
    default_model = ollama.get("default_model", "llama3.1:8b")

    agents_config = config.get("agents", {})
    persistence = config.get("persistence", {})

    # Create LLMs
    sup_cfg = agents_config.get("supervisor", {})
    supervisor_llm = create_supervisor_llm(
        model=sup_cfg.get("model", default_model),
        base_url=base_url,
        temperature=temperature,
    )
    supervisor_sys = sup_cfg.get("system_prompt", "Route to researcher or coder.")

    res_cfg = agents_config.get("researcher", {})
    researcher_llm = create_researcher_llm(
        model=res_cfg.get("model", default_model),
        base_url=base_url,
        temperature=temperature,
    )
    researcher_sys = res_cfg.get("system_prompt", "Answer general questions.")

    cod_cfg = agents_config.get("coder", {})
    coder_llm = create_coder_llm(
        model=cod_cfg.get("model", default_model),
        base_url=base_url,
        temperature=temperature,
    )
    coder_sys = cod_cfg.get("system_prompt", "Handle code and files with care.")

    # Supervisor node
    def _supervisor(s: KyberState) -> dict:
        return supervisor_node(s, supervisor_llm, supervisor_sys)

    # Researcher node
    def _researcher(s: KyberState) -> dict:
        return researcher_node(s, researcher_llm, researcher_sys)

    # Coder: agent + tools (for ReAct loop)
    coder_agent = create_coder_node(coder_llm, coder_sys)
    coder_tools = ToolNode(CODER_TOOLS)

    # Coder subgraph: agent <-> tools
    coder_builder = StateGraph(KyberState)
    coder_builder.add_node("coder_agent", coder_agent)
    coder_builder.add_node("coder_tools", coder_tools)
    coder_builder.add_edge(START, "coder_agent")
    coder_builder.add_conditional_edges("coder_agent", _should_continue_coder)
    coder_builder.add_edge("coder_tools", "coder_agent")
    coder_subgraph = coder_builder.compile()

    # Main graph: supervisor -> researcher | coder
    builder = StateGraph(KyberState)
    builder.add_node("supervisor", _supervisor)
    builder.add_node("researcher", _researcher)
    builder.add_node("coder", coder_subgraph)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", _route_after_supervisor)
    builder.add_edge("researcher", END)
    builder.add_edge("coder", END)

    # Persistence: AsyncSqliteSaver -> state.db
    global _checkpointer_cm, _checkpointer
    
    if _checkpointer is None:
        sqlite_path = persistence.get("sqlite_path", "state.db")
        _checkpointer_cm = AsyncSqliteSaver.from_conn_string(sqlite_path)
        _checkpointer = await _checkpointer_cm.__aenter__()
    
    graph = builder.compile(checkpointer=_checkpointer)
    return graph


async def get_graph():
    """Get the compiled graph (singleton-style for app)."""
    return await build_graph()
