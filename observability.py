"""Kyber Command - Phoenix/OpenInference observability for agent tracing."""

import os
from pathlib import Path

import yaml


def load_observability_config(config_path: str = "config.yaml") -> dict:
    """Load observability section from config."""
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("observability", {})


def init_phoenix(config: dict | None = None) -> None:
    """
    Initialize Phoenix OpenInference tracing for LangChain/LangGraph.
    Call this once at app startup, before any LLM or graph invocations.

    Expects a Phoenix server at http://localhost:6006 (start with: phoenix serve)
    """
    try:
        from phoenix.otel import register
    except ImportError:
        return  # Phoenix not installed, skip

    cfg = config or load_observability_config()
    project_name = cfg.get("project_name", "kyber-command")
    endpoint = cfg.get("phoenix_collector_endpoint", "http://localhost:6006")

    # Phoenix SDK reads these env vars; set before register
    os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", endpoint)
    os.environ.setdefault("PHOENIX_PROJECT_NAME", project_name)

    register(
        project_name=project_name,
        auto_instrument=True,
    )
