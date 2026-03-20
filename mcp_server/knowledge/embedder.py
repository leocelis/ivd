# mcp_server/knowledge/embedder.py

"""
OpenAI embedding generation and similarity search.
"""

from typing import Dict, List

import numpy as np
import openai
import tiktoken
from termcolor import colored

from mcp_server.knowledge.config import (
    EMBEDDING_MAX_BATCH_TOKENS,
    EMBEDDING_MODEL,
    get_embedding_cost,
)

# Lazy-initialized OpenAI client and token encoder
_client = None
_enc = None


def _get_client():
    """Lazy init — only create when embeddings are actually needed."""
    global _client
    if _client is None:
        _client = openai.OpenAI()
    return _client


def _get_encoder():
    """Lazy init — tiktoken encoding."""
    global _enc
    if _enc is None:
        _enc = tiktoken.get_encoding("cl100k_base")
    return _enc


def _num_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding."""
    return len(_get_encoder().encode(text))


def generate_embeddings(texts: List[str], show_cost: bool = True) -> Dict:
    """
    Generate embeddings for list of texts using OpenAI.

    Args:
        texts: List of text strings to embed
        show_cost: Whether to print cost information

    Returns:
        {'embeddings': np.ndarray, 'total_tokens': int, 'cost_usd': float}
    """
    text_tokens = [(text, _num_tokens(text)) for text in texts]
    total_tokens = sum(tokens for _, tokens in text_tokens)

    # Conservative batch limit (50% of max — tiktoken counts can differ from API)
    safe_limit = int(EMBEDDING_MAX_BATCH_TOKENS * 0.50)

    if total_tokens > safe_limit:
        print(colored(f"  Large input: {total_tokens:,} tokens, splitting into batches", "yellow"))

        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_tokens = 0

        for text, tokens in text_tokens:
            if current_tokens + tokens > safe_limit and current_batch:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = tokens
            else:
                current_batch.append(text)
                current_tokens += tokens
        if current_batch:
            batches.append(current_batch)

        all_embeddings = []
        total_cost = 0.0

        for i, batch in enumerate(batches, 1):
            batch_tokens = sum(_num_tokens(t) for t in batch)
            print(colored(f"  Batch {i}/{len(batches)}: {len(batch)} chunks, {batch_tokens:,} tokens", "blue"))

            response = _get_client().embeddings.create(input=batch, model=EMBEDDING_MODEL)
            batch_embeddings = np.array([d.embedding for d in response.data])
            all_embeddings.append(batch_embeddings)
            total_cost += get_embedding_cost(EMBEDDING_MODEL, batch_tokens)

        embeddings = np.vstack(all_embeddings)

        if show_cost:
            print(colored(f"  Embedded {len(embeddings)} chunks (${total_cost:.6f})", "green"))

        return {"embeddings": embeddings, "total_tokens": total_tokens, "cost_usd": total_cost}

    # Single batch
    print(colored(f"  Generating embeddings: {len(texts)} texts ({total_tokens} tokens)", "cyan"))

    response = _get_client().embeddings.create(input=texts, model=EMBEDDING_MODEL)
    embeddings = np.array([d.embedding for d in response.data])
    cost_usd = get_embedding_cost(EMBEDDING_MODEL, total_tokens)

    if show_cost:
        print(colored(f"  Embedded {len(embeddings)} chunks (${cost_usd:.6f})", "green"))

    return {"embeddings": embeddings, "total_tokens": total_tokens, "cost_usd": cost_usd}


def find_most_similar(
    query_embedding: np.ndarray,
    embeddings: np.ndarray,
    top_k: int = 5,
) -> List[Dict]:
    """
    Find top-k most similar embeddings to query.

    OpenAI embeddings are normalized, so dot product = cosine similarity.

    Returns:
        List of {'index': int, 'similarity': float}
    """
    similarities = np.dot(embeddings, query_embedding)
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [
        {"index": int(idx), "similarity": float(similarities[idx])}
        for idx in top_indices
    ]
