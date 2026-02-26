"""Pytest fixtures for Kyber Command tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """Path to a temporary config file."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("""
ollama:
  base_url: "http://localhost:11434"
  default_model: "llama3.1:8b"
  temperature: 0.7
agents:
  supervisor:
    model: "llama3.1:8b"
    system_prompt: "Route to researcher or coder."
  researcher:
    model: "llama3.1:8b"
    system_prompt: "Answer general questions."
  coder:
    model: "llama3.1:8b"
    system_prompt: "Handle code and files."
persistence:
  sqlite_path: ":memory:"
""", encoding="utf-8")
    return cfg


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Temporary directory for file tool tests."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.txt").write_text("hello world", encoding="utf-8")
    return tmp_path
