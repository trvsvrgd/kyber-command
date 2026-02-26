"""Researcher agent - handles general information and factual questions."""

from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .state import KyberState


def create_researcher_llm(model: str, base_url: str, temperature: float) -> ChatOllama:
    """Create the researcher LLM from config."""
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


def researcher_node(
    state: KyberState,
    llm: ChatOllama,
    system_prompt: str,
) -> dict:
    """
    Researcher node: answers general information questions.
    No tools, no file access, no HITL required.
    """
    messages = state["messages"]

    prompt_messages = [SystemMessage(content=system_prompt)] + list(messages)
    response = llm.invoke(prompt_messages)

    if isinstance(response, AIMessage):
        ai_message = response
    else:
        ai_message = AIMessage(content=str(response))

    return {"messages": [ai_message]}
