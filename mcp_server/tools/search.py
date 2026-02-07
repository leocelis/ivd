# mcp_server/tools/search.py

"""Tool: ivd_search — semantic search across IVD framework docs."""

import json
import os

from termcolor import colored

from mcp_server.knowledge.brain import get_brain_root, load_kb_embeddings
from mcp_server.knowledge.embedder import generate_embeddings, find_most_similar

LOG = "IVD Tools"


def ivd_search_tool(query: str, top_k: int = 5) -> str:
    """Semantic search across IVD framework documentation."""
    print(colored(f"[{LOG}] ivd_search: '{query}' (top_k={top_k})", "cyan"))

    brain_root = get_brain_root()

    if not os.path.exists(brain_root):
        print(colored(f"[{LOG}] Brain root not found: {brain_root}", "red"))
        return json.dumps({
            "error": "Knowledge base not found",
            "brain_root": brain_root,
            "suggestion": "Generate embeddings first. See migration_plan.md Step 4.",
            "alternative": "Use ivd_get_context, ivd_load_recipe, or ivd_load_template instead.",
        }, indent=2)

    # Load embeddings from all KB subdirectories
    import numpy as np
    all_embeddings = []
    all_metadata = []

    for kb_name in os.listdir(brain_root):
        kb_path = os.path.join(brain_root, kb_name)
        if os.path.isdir(kb_path):
            embeddings, metadata = load_kb_embeddings(kb_path)
            if len(embeddings) > 0:
                all_embeddings.append(embeddings)
                all_metadata.extend(metadata)

    if not all_embeddings:
        return json.dumps({
            "error": "No embeddings found in brain/",
            "suggestion": "Generate embeddings first.",
            "alternative": "Use ivd_get_context, ivd_load_recipe, or ivd_load_template instead.",
        }, indent=2)

    combined = np.vstack(all_embeddings)
    print(colored(f"[{LOG}] Loaded {len(combined)} chunks from {len(all_embeddings)} KBs", "blue"))

    try:
        query_result = generate_embeddings([query], show_cost=False)
        query_embedding = query_result["embeddings"][0]
    except Exception as e:
        return json.dumps({
            "error": f"Embedding generation failed: {e}",
            "alternative": "Use ivd_get_context, ivd_load_recipe, or ivd_load_template instead.",
        }, indent=2)

    results = find_most_similar(query_embedding, combined, top_k)

    for r in results:
        r.update(all_metadata[r["index"]])

    output = []
    for i, r in enumerate(results, 1):
        block = f"**Result {i}** (similarity: {r['similarity']:.2f})\n"
        block += f"Source: `{r['file_name']}`\n\n"
        text = r["chunk_text"][:800]
        if len(r["chunk_text"]) > 800:
            text += "..."
        block += text
        output.append(block)

    print(colored(f"[{LOG}] Found {len(results)} relevant chunks", "green"))
    return "\n\n---\n\n".join(output)
