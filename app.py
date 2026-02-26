"""Kyber Command - Chainlit entry point with HITL approval UI."""

import uuid

import chainlit as cl
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.types import Command

from graph_engine import build_graph, load_config
from observability import init_phoenix

# Init Phoenix tracing before any graph/LLM usage
init_phoenix()

# Build graph once at module load
_config = load_config()
_graph = build_graph(_config)


def _get_thread_id() -> str:
    """Get or create thread_id for this chat session."""
    tid = cl.user_session.get("thread_id")
    if tid:
        return str(tid)
    tid = str(uuid.uuid4())
    cl.user_session.set("thread_id", tid)
    return tid


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with thread_id for persistence."""
    thread_id = _get_thread_id()
    cl.user_session.set("thread_id", thread_id)
    await cl.Message(
        content=f"**Kyber Command** ready. Session ID: `{thread_id[:8]}...`\n\n"
        "Ask anything—I'll route you to the Researcher (general info) or Coder (Python/files). "
        "File writes require your approval.",
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages: stream graph execution and detect interrupts."""
    thread_id = _get_thread_id()
    config = {"configurable": {"thread_id": thread_id}}

    # Skip if we're waiting for a resume (user must use action buttons)
    if cl.user_session.get("awaiting_resume"):
        await cl.Message(
            content="Please use the **Approve**, **Modify**, or **Reject** button above to continue.",
        ).send()
        return

    user_content = message.content or ""
    if not user_content.strip():
        await cl.Message(content="Please enter a message.").send()
        return

    msg = cl.Message(content="")
    await msg.send()

    try:
        # Use astream to get messages + updates (for interrupt detection)
        interrupt_payload = None
        async for event in _graph.astream(
            {"messages": [HumanMessage(content=user_content)]},
            stream_mode=["messages", "updates"],
            config=config,
            subgraphs=True,
        ):
            # astream yields (mode, chunk) with multiple stream modes
            if isinstance(event, tuple) and len(event) == 2:
                mode, chunk = event
            else:
                mode, chunk = "values", event
            if mode == "messages":
                msg_chunk = chunk[0] if isinstance(chunk, (tuple, list)) else chunk
                if isinstance(msg_chunk, AIMessageChunk) and msg_chunk.content:
                    msg.content += msg_chunk.content
                    await msg.update()
            elif mode == "updates":
                # Check for __interrupt__ in updates (may be nested)
                to_check = chunk if isinstance(chunk, dict) else {}
                if "__interrupt__" in to_check:
                    interrupts = to_check["__interrupt__"]
                    if interrupts:
                        intr = interrupts[0]
                        payload = intr.value if hasattr(intr, "value") else intr
                        interrupt_payload = payload
                        break
                # Also check nested node updates
                for node_data in (to_check.values() if isinstance(to_check, dict) else []):
                    if isinstance(node_data, dict) and "__interrupt__" in node_data:
                        interrupts = node_data["__interrupt__"]
                        if interrupts:
                            intr = interrupts[0]
                            payload = intr.value if hasattr(intr, "value") else intr
                            interrupt_payload = payload
                            break

        await msg.update()

        if interrupt_payload:
            await _show_hitl_ui(interrupt_payload, thread_id)

    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()


async def _show_hitl_ui(payload: dict, thread_id: str):
    """Display HITL approval UI with Approve, Modify, Reject buttons."""
    action = payload.get("action", "unknown")
    path = payload.get("path", "")
    preview = payload.get("preview", payload.get("content", "")[:500])
    msg_text = payload.get("message", "Approve this action?")

    cl.user_session.set("awaiting_resume", True)
    cl.user_session.set("hitl_payload", payload)
    cl.user_session.set("hitl_thread_id", thread_id)

    actions = [
        cl.Action(name="approve", value="approve", label="✅ Approve"),
        cl.Action(name="reject", value="reject", label="❌ Reject"),
        cl.Action(name="modify", value="modify", label="✏️ Modify"),
    ]

    content = f"**Human approval required**\n\n{msg_text}\n\n"
    if path:
        content += f"**Path:** `{path}`\n\n"
    if preview:
        content += f"**Preview:**\n```\n{preview}\n```"

    await cl.Message(content=content, actions=actions).send()


@cl.action_callback("approve")
async def on_approve(action: cl.Action):
    """Handle Approve button: resume graph with approval."""
    await _resume_with_decision("approve")


@cl.action_callback("reject")
async def on_reject(action: cl.Action):
    """Handle Reject button: resume graph with rejection."""
    await _resume_with_decision("reject")


@cl.action_callback("modify")
async def on_modify(action: cl.Action):
    """Handle Modify: for now, prompt user to type modifications (simplified)."""
    payload = cl.user_session.get("hitl_payload")
    if not payload:
        await cl.Message(content="Session expired. Please send a new message.").send()
        return
    # Simplified: treat Modify as Reject (user can retry with new request)
    await cl.Message(
        content="**Modify** is not yet interactive. Use **Reject** and send a new message with your desired changes.",
    ).send()
    await _resume_with_decision("reject")


async def _resume_with_decision(decision: str):
    """Resume the graph with the user's HITL decision."""
    payload = cl.user_session.get("hitl_payload")
    thread_id = cl.user_session.get("hitl_thread_id")
    if not payload or not thread_id:
        await cl.Message(content="Session expired. Please send a new message.").send()
        cl.user_session.set("awaiting_resume", False)
        return

    cl.user_session.set("awaiting_resume", False)
    cl.user_session.set("hitl_payload", None)
    cl.user_session.set("hitl_thread_id", None)

    resume_value = {"decision": decision}
    if decision == "approve":
        resume_value["path"] = payload.get("path")
        resume_value["content"] = payload.get("content")

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await _graph.ainvoke(
            Command(resume=resume_value),
            config=config,
        )

        # Extract final AI message for display
        messages = result.get("messages", [])
        for m in reversed(messages):
            if hasattr(m, "content") and m.content:
                await cl.Message(content=m.content).send()
                break

        # Check for another interrupt (e.g., multi-tool scenario)
        if "__interrupt__" in result and result["__interrupt__"]:
            intr = result["__interrupt__"][0]
            pl = intr.value if hasattr(intr, "value") else intr
            await _show_hitl_ui(pl, thread_id)

    except Exception as e:
        await cl.Message(content=f"Error resuming: {e}").send()
