# mcp_server/knowledge/__init__.py

"""
Knowledge base: embedding storage, search, and text processing.
"""

from mcp_server.knowledge.brain import get_brain_root, load_kb_embeddings
from mcp_server.knowledge.embedder import generate_embeddings, find_most_similar
from mcp_server.knowledge.processor import extract_text, simple_chunk_text

__all__ = [
    "get_brain_root",
    "load_kb_embeddings",
    "generate_embeddings",
    "find_most_similar",
    "extract_text",
    "simple_chunk_text",
]
