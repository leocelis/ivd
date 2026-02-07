#!/usr/bin/env python3
# mcp_server/devops/embed.py

"""
Generate IVD knowledge base embeddings.

Scans the IVD repo root for framework docs, book chapters, recipes, templates,
and research — then generates OpenAI embeddings stored in mcp_server/brain/.

Usage:
    python mcp_server/devops/embed.py              # full run
    python mcp_server/devops/embed.py --dry-run    # scan only, no API calls
    python mcp_server/devops/embed.py --force       # re-embed everything (ignore cache)

Requires OPENAI_API_KEY in environment (loaded from .env by embed.sh wrapper).
"""

import argparse
import sys
from pathlib import Path

# Add repo root to path so mcp_server is importable
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

from termcolor import colored

from mcp_server.knowledge.brain import (
    create_kb,
    get_brain_root,
    process_and_store,
    scan_directory,
)

KB_NAME = "ivd"


def main():
    parser = argparse.ArgumentParser(description="Generate IVD embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, no API calls")
    parser.add_argument("--force", action="store_true", help="Re-embed everything")
    args = parser.parse_args()

    print(colored("=" * 60, "magenta"))
    print(colored("  IVD Embedding Generator", "magenta"))
    print(colored("=" * 60, "magenta"))

    source = str(REPO_ROOT)
    brain_root = get_brain_root()

    print(colored(f"\n  Source:  {source}", "cyan"))
    print(colored(f"  Output:  {brain_root}/{KB_NAME}/", "cyan"))
    print(colored(f"  Mode:    {'DRY RUN' if args.dry_run else 'LIVE'}", "yellow" if args.dry_run else "green"))

    # Scan files
    print(colored(f"\n  Scanning...", "cyan"))
    files = scan_directory(source)

    if not files:
        print(colored("  No supported files found!", "red"))
        sys.exit(1)

    # Group by directory for readable output
    dirs = {}
    for f in files:
        rel = Path(f["path"]).relative_to(REPO_ROOT)
        d = str(rel.parent) if str(rel.parent) != "." else "(root)"
        dirs.setdefault(d, []).append(rel.name)

    print(colored(f"\n  Found {len(files)} files across {len(dirs)} directories:\n", "green"))
    for d in sorted(dirs.keys()):
        print(colored(f"    {d}/", "blue"))
        for name in sorted(dirs[d]):
            print(f"      {name}")

    total_size = sum(f["size"] for f in files)
    print(colored(f"\n  Total: {len(files)} files, {total_size:,} bytes", "green"))

    if args.dry_run:
        print(colored("\n  Dry run complete. No embeddings generated.", "yellow"))
        return

    # Create / open knowledge base
    kb_path = create_kb(KB_NAME, source)
    print(colored(f"\n  Knowledge base: {kb_path}", "cyan"))
    print(colored(f"  Processing...\n", "cyan"))

    stats = {"processed": 0, "skipped": 0, "errors": 0, "cost": 0.0}

    for f in files:
        try:
            result = process_and_store(kb_path, f, skip_if_exists=not args.force)
            if result["status"] == "processed":
                stats["processed"] += 1
                stats["cost"] += result["cost_usd"]
            elif result["status"] == "skipped":
                stats["skipped"] += 1
        except Exception as e:
            print(colored(f"  ERROR: {f['name']}: {e}", "red"))
            stats["errors"] += 1

    print(colored(f"\n{'=' * 60}", "magenta"))
    print(colored(f"  Done!", "green"))
    print(colored(f"  Processed: {stats['processed']}", "green"))
    print(colored(f"  Skipped:   {stats['skipped']} (unchanged)", "yellow"))
    print(colored(f"  Errors:    {stats['errors']}", "red" if stats["errors"] else "green"))
    print(colored(f"  Cost:      ${stats['cost']:.6f}", "cyan"))
    print(colored(f"{'=' * 60}", "magenta"))


if __name__ == "__main__":
    main()
