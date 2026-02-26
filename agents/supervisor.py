"""Supervisor agent - routes queries to Researcher or Coder."""

from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .state import KyberState, ROUTER_CODER, ROUTER_RESEARCHER


def create_supervisor_llm(model: str, base_url: str, temperature: float) -> ChatOllama:
    """Create the supervisor LLM from config."""
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


def supervisor_node(
    state: KyberState,
    llm: ChatOllama,
    system_prompt: str,
) -> dict:
    """
    Supervisor node: analyzes the latest user message and routes to Researcher or Coder.
    """
    messages = state["messages"]
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return {"next_agent": ROUTER_RESEARCHER}

    prompt = f"{system_prompt}\n\nUser query: {last_message.content}"
    response = llm.invoke(
        [SystemMessage(content=system_prompt), last_message]
    )

    if isinstance(response, AIMessage):
        content = (response.content or "").strip().upper()
    else:
        content = str(response).strip().upper()

    if "CODER" in content or "CODE" in content or "FILE" in content:
        return {"next_agent": ROUTER_CODER}
    return {"next_agent": ROUTER_RESEARCHER}
