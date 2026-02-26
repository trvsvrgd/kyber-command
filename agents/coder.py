"""Coder agent - handles Python and filesystem tasks with HITL approval."""

from pathlib import Path

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt

from .state import KyberState


def create_coder_llm(model: str, base_url: str, temperature: float) -> ChatOllama:
    """Create the coder LLM from config."""
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
    )


@tool
def read_file(path: str) -> str:
    """Read the contents of a file. Path should be relative to workspace or absolute."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. REQUIRES HUMAN APPROVAL before execution.
    Path should be relative to workspace or absolute.
    """
    # HITL: Pause before any write; payload surfaces in result["__interrupt__"]
    response = interrupt({
        "action": "write_file",
        "path": path,
        "content": content,
        "message": f"Approve writing to {path}?",
        "preview": content[:500] + ("..." if len(content) > 500 else ""),
    })

    decision = response.get("decision", "reject")
    if decision == "reject":
        return "File write cancelled by user."

    # Use modified path/content if user provided them
    final_path = response.get("path", path)
    final_content = response.get("content", content)

    try:
        Path(final_path).parent.mkdir(parents=True, exist_ok=True)
        Path(final_path).write_text(final_content, encoding="utf-8")
        return f"Successfully wrote to {final_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    try:
        items = list(Path(path).iterdir())
        lines = [f"  {p.name}/" if p.is_dir() else f"  {p.name}" for p in sorted(items)]
        return "\n".join(lines) if lines else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


CODER_TOOLS = [read_file, write_file, list_directory]


def create_coder_node(llm: ChatOllama, system_prompt: str):
    """Create the coder node with tools bound to the LLM."""

    llm_with_tools = llm.bind_tools(CODER_TOOLS)

    def coder_node(state: KyberState) -> dict:
        messages = state["messages"]

        prompt_messages = [SystemMessage(content=system_prompt)] + list(messages)
        response = llm_with_tools.invoke(prompt_messages)

        if not response.tool_calls:
            return {"messages": [response]}

        # Process tool calls (interrupt may occur inside tools)
        tool_messages = []
        for tc in response.tool_calls:
            tool = next((t for t in CODER_TOOLS if t.name == tc["name"]), None)
            if tool:
                result = tool.invoke(tc.get("args", {}))
                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )

        return {"messages": [response] + tool_messages}

    return coder_node
