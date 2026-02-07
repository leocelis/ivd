# mcp_server/knowledge/processor.py

"""
Text extraction and chunking for IVD knowledge base.

IVD only has .md, .yaml, .txt files — no PDF/DOCX converters needed.
"""

from pathlib import Path
from typing import List, Optional

from mcp_server.knowledge.config import (
    CHUNK_SIZE_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    estimate_chars_from_tokens,
)


def extract_text(file_path: str) -> Optional[str]:
    """
    Extract text from a file.

    IVD framework only contains plain-text formats (.md, .yaml, .txt, etc.)
    so we just read the file directly. No PDF/DOCX converters needed.

    Args:
        file_path: Path to file

    Returns:
        File text content, or None if reading failed
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def simple_chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> List[str]:
    """
    Chunk text by character count with overlap.

    Research-validated: 800 tokens ~= 3200 chars (avg 4 chars/token).

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        overlap: Overlap size in tokens

    Returns:
        List of text chunks
    """
    char_chunk_size = estimate_chars_from_tokens(chunk_size)
    char_overlap = estimate_chars_from_tokens(overlap)

    chunks = []
    start = 0

    while start < len(text):
        end = start + char_chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += char_chunk_size - char_overlap

    return chunks
