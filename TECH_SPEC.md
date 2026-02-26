# Project Technical Specification

## High-Level Intent
Kyber Command is a **localized multi-agent coordination hub** that powers specialized droids (Researcher, Coder) with local LLMs via Ollama. It provides a human-in-the-loop interface via Chainlit with Phoenix observability—ensuring no agent modifies files without explicit approval.

## Core Requirements
- **Supervisor routing**: Classify user queries and route to Researcher (general info) or Coder (Python/filesystem).
- **Researcher agent**: Answer factual questions with no tools or file access.
- **Coder agent**: Read, list, and write files—all writes require HITL approval before execution.
- **Persistence**: SQLite-backed checkpointing (LangGraph SqliteSaver) so sessions survive restarts.
- **Observability**: Phoenix at `http://localhost:6006` for tracing agent chains.

## Tech Stack & Constraints
- **Language/Framework:** Python 3.11+, LangGraph, LangChain
- **Key Libraries:** langgraph, langgraph-checkpoint-sqlite, langchain-ollama, chainlit, arize-phoenix, pydantic, pyyaml
- **Storage/Data:** SQLite (`state.db`), local filesystem via Coder tools
- **Style Preferences:** Modular agents, config-driven prompts in `config.yaml`, TypedDict/Pydantic state, docstrings required

## Out of Scope
- Cloud-hosted LLMs (OpenAI, Anthropic)—Ollama/local only.
- Multi-user auth or RBAC.
- Data warehouse / Databricks / Unity Catalog integration.
- Building new agents beyond Researcher and Coder without spec update.
