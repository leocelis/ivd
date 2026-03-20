# mcp_server/knowledge/config.py

"""
Knowledge Base & Embeddings Configuration.

OpenAI embeddings config for document processing and semantic search.
"""

from typing import Set

# =============================================================================
# EMBEDDING MODELS
# =============================================================================

EMBEDDING_MODEL = "text-embedding-3-small"  # $0.00002/1K tokens, 1536 dims
EMBEDDING_MODEL_LARGE = "text-embedding-3-large"  # $0.00013/1K tokens, 3072 dims

EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

EMBEDDING_COSTS = {
    "text-embedding-3-small": 0.00002,
    "text-embedding-3-large": 0.00013,
}

# =============================================================================
# EMBEDDING API LIMITS
# =============================================================================

EMBEDDING_MAX_TOKENS = 8191
EMBEDDING_MAX_BATCH_TOKENS = 300000
EMBEDDING_MAX_ARRAY_SIZE = 2048

# =============================================================================
# BRAIN STORAGE
# =============================================================================

# Relative to mcp_server/ directory
BRAIN_DIR_NAME = "brain"

# =============================================================================
# CHUNKING (research-validated: 800 tokens, 20% overlap)
# =============================================================================

CHUNK_SIZE_TOKENS = 800
CHUNK_OVERLAP_TOKENS = 160
CHARS_PER_TOKEN = 4  # approximate

# =============================================================================
# SUPPORTED FILE TYPES (IVD only needs text-based formats)
# =============================================================================

SUPPORTED_EXTENSIONS: Set[str] = {
    ".md", ".markdown", ".txt",
    ".yaml", ".yml",
    ".py", ".js", ".ts",
    ".json", ".toml",
    ".sh", ".bash",
    ".rst", ".adoc",
}

# =============================================================================
# UTILITIES
# =============================================================================


def get_embedding_cost(model: str, tokens: int) -> float:
    """Calculate embedding cost in USD."""
    cost_per_1k = EMBEDDING_COSTS.get(model, 0.00002)
    return (tokens / 1000) * cost_per_1k


def estimate_chars_from_tokens(tokens: int) -> int:
    """Estimate character count from token count."""
    return tokens * CHARS_PER_TOKEN
