# mcp_server/knowledge/brain.py

"""
Brain operations — knowledge base storage and retrieval.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from termcolor import colored

from mcp_server.knowledge.config import SUPPORTED_EXTENSIONS
from mcp_server.knowledge.embedder import generate_embeddings
from mcp_server.knowledge.processor import extract_text, simple_chunk_text


def get_brain_root() -> str:
    """Get path to brain root directory (mcp_server/brain/)."""
    return str(Path(__file__).parent.parent / "brain")


# Convention: any directory whose name starts with PRIVATE_PREFIX is treated
# as private content and excluded from embedding scans. The canonical example
# Private maintainer content belongs outside this OSS repo (separate private git repo).
# SKIP_DIRS still lists "_private" for underscore-prefix dirs if present.
# prefix is the single source of truth for "do not embed".
PRIVATE_PREFIX = "_"

# Directories to skip during embedding scans.
# Two layers of defense:
#   1. SKIP_DIRS — explicit names (this set), including `_private` for
#      grep-ability even though it would also be caught by PRIVATE_PREFIX.
#   2. PRIVATE_PREFIX — the `_*` and `.*` prefix rules in scan_directory.
# Both must agree that `_private/` is excluded; the test
# `test_brain_scan.py::test_private_dir_never_embedded` locks in the contract.
SKIP_DIRS = {
    "mcp_server",
    ".venv",
    "venv",
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    ".obsidian",
    ".pytest_cache",
    ".do",
    "deploy",
    "temp",
    "_private",
}

# Root-level files to skip (not IVD knowledge)
SKIP_FILES = {
    "requirements.txt",
}


def scan_directory(directory: str, extra_skip: set = None) -> List[Dict]:
    """
    Scan directory recursively for supported files.

    Skips:
      - Directories listed in SKIP_DIRS (e.g. mcp_server, deploy, _private).
      - Any directory whose name starts with PRIVATE_PREFIX ("_") — the
        underscore-prefix convention for private content (e.g. `_private/`,
        `_drafts/`). Never embedded; never shipped via ivd_search.
      - Any directory whose name starts with "." (dotfiles, e.g. `.git/`).
    """
    skip = SKIP_DIRS | (extra_skip or set())
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [
            d for d in dirs
            if d not in skip
            and not d.startswith(PRIVATE_PREFIX)
            and not d.startswith(".")
        ]
        rel_root = os.path.relpath(root, directory)
        for filename in filenames:
            rel_path = os.path.join(rel_root, filename) if rel_root != "." else filename
            if rel_path in SKIP_FILES:
                continue
            if Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS:
                file_path = os.path.join(root, filename)
                files.append(
                    {
                        "path": file_path,
                        "name": filename,
                        "size": os.path.getsize(file_path),
                    }
                )
    return files


def create_kb(kb_name: str, source_path: str) -> str:
    """Create brain subfolder structure. Returns kb_path."""
    kb_path = os.path.join(get_brain_root(), kb_name)
    os.makedirs(kb_path, exist_ok=True)

    index_path = os.path.join(kb_path, "index.json")
    if not os.path.exists(index_path):
        index = {
            "kb_name": kb_name,
            "source_path": ".",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "documents": {},
            "stats": {"total_docs": 0, "total_chunks": 0, "total_cost": 0.0},
        }
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)

    return kb_path


def load_index(kb_path: str) -> Dict:
    """Load index.json from knowledge base."""
    with open(os.path.join(kb_path, "index.json"), "r") as f:
        return json.load(f)


def update_index(kb_path: str, doc_hash: str, doc_data: Dict) -> None:
    """Update index with new/modified document."""
    index_path = os.path.join(kb_path, "index.json")
    index = load_index(kb_path)

    index["documents"][doc_hash] = {
        "file_name": doc_data["file_name"],
        "file_path": doc_data["file_path"],
        "num_chunks": doc_data["num_chunks"],
        "cost_usd": doc_data["cost_usd"],
        "processed_at": doc_data["processed_at"],
    }

    index["stats"]["total_docs"] = len(index["documents"])
    index["stats"]["total_chunks"] = sum(
        d["num_chunks"] for d in index["documents"].values()
    )
    index["stats"]["total_cost"] = sum(
        d["cost_usd"] for d in index["documents"].values()
    )
    index["last_updated"] = datetime.utcnow().isoformat()

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def file_hash(file_path: str) -> str:
    """SHA256 hash of file content for change detection."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_document_processed(kb_path: str, doc_hash: str) -> bool:
    """Check if document with this hash is already processed."""
    index = load_index(kb_path)
    return doc_hash in index["documents"]


def process_and_store(
    kb_path: str, file_info: Dict, skip_if_exists: bool = True,
    source_root: str = "",
) -> Dict:
    """Process single file: extract text -> chunk -> embed -> store."""
    fp = file_info["path"]
    dh = file_hash(fp)

    if skip_if_exists and is_document_processed(kb_path, dh):
        return {
            "status": "skipped",
            "doc_hash": dh,
            "cost_usd": 0.0,
            "reason": "already_processed",
        }

    print(colored(f"  Processing: {file_info['name']}", "cyan"))

    text = extract_text(fp)
    if not text or not text.strip():
        print(colored(f"  Skipped (empty or extraction failed)", "yellow"))
        return {"status": "skipped", "doc_hash": dh, "cost_usd": 0.0, "reason": "empty"}

    chunks = simple_chunk_text(text)
    print(colored(f"  {len(chunks)} chunks", "blue"))

    result = generate_embeddings(chunks, show_cost=False)
    embeddings = result["embeddings"]
    cost = result["cost_usd"]

    np.save(os.path.join(kb_path, f"{dh}.npy"), embeddings)

    rel_path = os.path.relpath(fp, source_root) if source_root else fp
    metadata = {
        "doc_hash": dh,
        "file_path": rel_path,
        "file_name": file_info["name"],
        "num_chunks": len(chunks),
        "chunks": chunks,
        "cost_usd": cost,
        "processed_at": datetime.utcnow().isoformat(),
    }
    with open(os.path.join(kb_path, f"{dh}.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    update_index(kb_path, dh, metadata)
    print(colored(f"  Saved ({len(chunks)} embeddings, ${cost:.6f})", "green"))

    return {"status": "processed", "doc_hash": dh, "cost_usd": cost}


def load_kb_embeddings(kb_path: str) -> Tuple[np.ndarray, List[Dict]]:
    """
    Load all embeddings from a knowledge base.

    Returns:
        (embeddings_matrix, chunk_metadata_list)
    """
    all_embeddings = []
    all_metadata = []

    for file in os.listdir(kb_path):
        if file.endswith(".npy"):
            emb_path = os.path.join(kb_path, file)
            embeddings = np.load(emb_path)

            doc_hash = file.replace(".npy", "")
            meta_path = os.path.join(kb_path, f"{doc_hash}.json")

            with open(meta_path, "r") as f:
                meta = json.load(f)

            for i, chunk in enumerate(meta["chunks"]):
                all_metadata.append(
                    {
                        "kb_name": Path(kb_path).name,
                        "file_name": meta["file_name"],
                        "file_path": meta["file_path"],
                        "chunk_index": i,
                        "chunk_text": chunk,
                    }
                )

            all_embeddings.append(embeddings)

    if not all_embeddings:
        return np.array([]), []

    return np.vstack(all_embeddings), all_metadata
