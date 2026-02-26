"""Tests for config loading."""

from pathlib import Path

import pytest

from graph_engine import load_config


def test_load_config_success(config_path: Path) -> None:
    """load_config returns dict with expected structure."""
    cfg = load_config(str(config_path))
    assert "ollama" in cfg
    assert cfg["ollama"]["base_url"] == "http://localhost:11434"
    assert cfg["ollama"]["default_model"] == "llama3.1:8b"
    assert "agents" in cfg
    assert "supervisor" in cfg["agents"]
    assert "persistence" in cfg


def test_load_config_missing_raises() -> None:
    """load_config raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="Config not found"):
        load_config("nonexistent_config_xyz.yaml")
