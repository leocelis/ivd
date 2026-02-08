# mcp_server/tests/unit/test_search.py

"""Unit tests for ivd_search tool.

Note: ivd_search requires embeddings (brain/) and an OpenAI API key to generate
query embeddings. These tests verify error handling when dependencies are missing,
and correct behavior when brain exists. The actual semantic quality of search
results is validated by smoke tests against the live server.
"""

import json
import os
from unittest.mock import patch, MagicMock

from mcp_server.tools.search import ivd_search_tool


class TestIvdSearch:
    """Tests for ivd_search."""

    def test_returns_string(self):
        """Search always returns a string (either results or error JSON)."""
        result = ivd_search_tool("test query")
        assert isinstance(result, str)

    def test_missing_brain_returns_error(self):
        """When brain root doesn't exist, return structured error."""
        with patch("mcp_server.tools.search.get_brain_root", return_value="/tmp/nonexistent_brain_xyz"):
            result = ivd_search_tool("test query")
            data = json.loads(result)
            assert "error" in data
            assert "suggestion" in data or "alternative" in data

    def test_empty_brain_returns_error(self, tmp_path):
        """When brain exists but has no embeddings, return error."""
        brain_dir = tmp_path / "brain"
        brain_dir.mkdir()
        with patch("mcp_server.tools.search.get_brain_root", return_value=str(brain_dir)):
            result = ivd_search_tool("test query")
            data = json.loads(result)
            assert "error" in data

    def _create_fake_brain(self, tmp_path, num_chunks=5, dim=10):
        """Helper: create a fake brain directory with .npy and .json files.

        The brain expects paired files: <hash>.npy + <hash>.json where the JSON
        has {"file_name": ..., "file_path": ..., "chunks": [text, text, ...]}.
        """
        import numpy as np
        import json as json_mod

        brain_dir = tmp_path / "brain"
        kb_dir = brain_dir / "test_kb"
        kb_dir.mkdir(parents=True)

        doc_hash = "abc123"
        embeddings = np.random.rand(num_chunks, dim).astype(np.float32)
        np.save(str(kb_dir / f"{doc_hash}.npy"), embeddings)

        metadata = {
            "file_name": "test_doc.md",
            "file_path": "docs/test_doc.md",
            "chunks": [f"Test content for chunk {i}" for i in range(num_chunks)],
        }
        (kb_dir / f"{doc_hash}.json").write_text(json_mod.dumps(metadata))

        return brain_dir

    def test_embedding_failure_returns_error(self, tmp_path):
        """When embedding generation fails, return structured error."""
        brain_dir = self._create_fake_brain(tmp_path)

        with patch("mcp_server.tools.search.get_brain_root", return_value=str(brain_dir)):
            with patch("mcp_server.tools.search.generate_embeddings", side_effect=Exception("API key not set")):
                result = ivd_search_tool("test query")
                data = json.loads(result)
                assert "error" in data
                assert "API key" in data["error"] or "failed" in data["error"].lower()

    def test_successful_search_returns_results(self, tmp_path):
        """When brain and API work, return formatted results."""
        import numpy as np

        brain_dir = self._create_fake_brain(tmp_path, num_chunks=5, dim=10)

        mock_query_result = {
            "embeddings": [np.random.rand(10).tolist()],
            "total_tokens": 10,
        }

        with patch("mcp_server.tools.search.get_brain_root", return_value=str(brain_dir)):
            with patch("mcp_server.tools.search.generate_embeddings", return_value=mock_query_result):
                result = ivd_search_tool("test query", top_k=3)
                assert "Result 1" in result
                assert "similarity" in result
