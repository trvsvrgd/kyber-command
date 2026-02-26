"""Tests for Coder tools (read_file, list_directory)."""

from pathlib import Path

import pytest

from agents.coder import list_directory, read_file


class TestReadFile:
    """Tests for read_file tool."""

    def test_reads_existing_file(self, temp_workspace: Path) -> None:
        path = str(temp_workspace / "file.txt")
        result = read_file.invoke({"path": path})
        assert result == "hello world"

    def test_returns_error_for_missing_file(self) -> None:
        result = read_file.invoke({"path": "/nonexistent/path/xyz.txt"})
        assert "Error" in result
        assert "not found" in result.lower() or "File not found" in result


class TestListDirectory:
    """Tests for list_directory tool."""

    def test_lists_files_and_dirs(self, temp_workspace: Path) -> None:
        result = list_directory.invoke({"path": str(temp_workspace)})
        assert "file.txt" in result
        assert "subdir/" in result

    def test_default_path_current_dir(self) -> None:
        """Default path '.' lists current working directory."""
        result = list_directory.invoke({})
        assert result
        assert not result.startswith("Error")

    def test_returns_error_for_missing_path(self) -> None:
        result = list_directory.invoke({"path": "/nonexistent/path/xyz"})
        assert "Error" in result
