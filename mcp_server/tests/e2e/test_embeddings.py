# mcp_server/tests/e2e/test_embeddings.py

"""
End-to-end validation of IVD embeddings via ivd_search.

Verifies that committed embeddings (brain/ivd/) contain content from:
- Book chapters (private alpha content)
- Framework docs (framework.md, cookbook.md, etc.)
- Recipes
- Research documents

Each test queries for content that is unique to a specific source,
then validates the search returns relevant results from that source.

Requires: OPENAI_API_KEY in environment (for query embedding generation).
"""

import json
import os

import pytest

from mcp_server.registry import call_tool


# Skip entire module if no OpenAI API key (can't generate query embeddings)
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — cannot generate query embeddings",
)


def search(query: str, top_k: int = 3) -> dict:
    """Call ivd_search and parse the result."""
    result = call_tool("ivd_search", {"query": query, "top_k": top_k})
    # ivd_search returns markdown-formatted text, not raw JSON
    # Parse what we can; the key signal is the content in the response
    return {"raw": result, "has_results": "Result" in result or "result" in result}


def assert_contains(result: dict, *keywords: str):
    """Assert the search result contains at least one of the keywords."""
    raw = result["raw"].lower()
    found = [kw for kw in keywords if kw.lower() in raw]
    assert found, (
        f"Expected at least one of {keywords} in search results, "
        f"got: {result['raw'][:300]}..."
    )


# ---------------------------------------------------------------------------
# Book content (chapter.md files in book/manuscript/)
# ---------------------------------------------------------------------------

class TestBookEmbeddings:
    """Verify book content is included in embeddings."""

    def test_chapter_1_alignment_crisis(self):
        """Chapter 1 unique phrase: 'building at the speed of misunderstanding'."""
        result = search("building at the speed of misunderstanding")
        assert result["has_results"]
        assert_contains(result, "misunderstanding", "misalignment", "alignment")

    def test_chapter_1_prd_failure(self):
        """Chapter 1 discusses why PRDs fail with AI agents."""
        result = search("Why do PRDs and user stories fail with AI agents?")
        assert result["has_results"]
        assert_contains(result, "prd", "user stor", "prose", "verify")

    def test_chapter_1_many_turns(self):
        """Chapter 1 introduces the 'many turns' problem."""
        result = search("What is the many turns problem in AI development?")
        assert result["has_results"]
        assert_contains(result, "many turns", "turn", "hallucination")

    def test_chapter_2_ivd_paradigm(self):
        """Chapter 2 introduces the IVD paradigm shift."""
        result = search("How does IVD shift from human-written to AI-written intent?")
        assert result["has_results"]
        assert_contains(result, "intent", "ai writes", "paradigm", "shift")

    def test_chapter_3_principles_depth(self):
        """Chapter 3 has deep explanations of each principle."""
        result = search("What breaks without executable understanding in IVD?")
        assert result["has_results"]
        assert_contains(result, "executable", "prose", "fails", "loudly")


# ---------------------------------------------------------------------------
# Framework docs (framework.md, cookbook.md, etc.)
# ---------------------------------------------------------------------------

class TestFrameworkEmbeddings:
    """Verify framework documentation is included in embeddings."""

    def test_framework_principles(self):
        """framework.md contains the canonical 8 principles."""
        result = search("What are the eight immutable principles of IVD?")
        assert result["has_results"]
        assert_contains(result, "principle", "immutable", "intent is primary")

    def test_cookbook_content(self):
        """cookbook.md contains practical implementation guidance."""
        result = search("How to create your first IVD intent artifact step by step?")
        assert result["has_results"]
        assert_contains(result, "intent", "artifact", "template", "scaffold")

    def test_workflow_level(self):
        """Framework docs describe workflow-level intents."""
        result = search("When should I use workflow level versus module level intent?")
        assert result["has_results"]
        assert_contains(result, "workflow", "module", "level", "step")


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

class TestRecipeEmbeddings:
    """Verify recipes are included in embeddings."""

    def test_agent_classifier_recipe(self):
        """The agent-classifier recipe should be findable."""
        result = search("How to build an AI classification agent with IVD recipe?")
        assert result["has_results"]
        assert_contains(result, "classifier", "agent", "recipe", "classification")

    def test_background_job_recipe(self):
        """The infra-background-job recipe should be findable."""
        result = search("Background job processing recipe with retry and idempotency")
        assert result["has_results"]
        assert_contains(result, "background", "job", "retry", "idempoten")


# ---------------------------------------------------------------------------
# Research documents
# ---------------------------------------------------------------------------

class TestResearchEmbeddings:
    """Verify research docs are included in embeddings."""

    def test_agent_knowledge_standards(self):
        """Research on MCP and agent knowledge sharing."""
        result = search("What is Model Context Protocol and how does it help AI agents?")
        assert result["has_results"]
        assert_contains(result, "mcp", "model context protocol", "agent")


# ---------------------------------------------------------------------------
# Embedding quality checks
# ---------------------------------------------------------------------------

class TestEmbeddingQuality:
    """Verify embeddings return relevant results, not random noise."""

    def test_relevance_for_specific_query(self):
        """A specific query should return content matching the topic."""
        result = search("How does Innovation through Inversion work in IVD?")
        assert result["has_results"]
        assert_contains(result, "inversion", "default", "invert", "principle 8")

    def test_different_queries_return_different_results(self):
        """Two different queries should return different content."""
        result1 = search("What is the alignment crisis?")
        result2 = search("How do recipes work in IVD?")

        # Both should have results
        assert result1["has_results"]
        assert result2["has_results"]

        # Results should be different (not identical)
        assert result1["raw"] != result2["raw"], "Two different queries returned identical results"

    def test_returns_source_attribution(self):
        """Search results should include source file information."""
        result = search("Intent is Primary principle")
        # Results should contain source file references
        assert_contains(result, ".md", ".yaml", "source")
