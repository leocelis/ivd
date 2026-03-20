#!/usr/bin/env python3
# mcp_server/devops/search.py

"""
Search IVD knowledge base from the command line.

Usage:
    python mcp_server/devops/search.py "What are the 8 IVD principles?"
    python mcp_server/devops/search.py "How do recipes work?" --top-k 3
    python mcp_server/devops/search.py "intent artifacts" --verbose

Requires OPENAI_API_KEY in environment (loaded from .env by search.sh wrapper).
"""

import argparse
import sys
from pathlib import Path

# Add repo root to path so mcp_server is importable
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

from termcolor import colored

from mcp_server.tools.search import ivd_search_tool


def main():
    parser = argparse.ArgumentParser(description="Search IVD knowledge base")
    parser.add_argument("query", help="Search query (natural language)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--verbose", action="store_true", help="Show full chunk text")
    args = parser.parse_args()

    print(colored(f"\n  Query: \"{args.query}\"", "cyan"))
    print(colored(f"  Top-K: {args.top_k}\n", "cyan"))

    result = ivd_search_tool(args.query, args.top_k)

    # Check for error response
    if result.startswith("{"):
        import json
        try:
            data = json.loads(result)
            if "error" in data:
                print(colored(f"  Error: {data['error']}", "red"))
                if "suggestion" in data:
                    print(colored(f"  Suggestion: {data['suggestion']}", "yellow"))
                sys.exit(1)
        except json.JSONDecodeError:
            pass

    if not args.verbose:
        # Trim each result chunk to ~400 chars for readable output
        lines = result.split("\n")
        trimmed = []
        char_count = 0
        for line in lines:
            if line.startswith("---"):
                trimmed.append(line)
                char_count = 0
            elif line.startswith("**Result"):
                trimmed.append(line)
                char_count = 0
            elif line.startswith("Source:"):
                trimmed.append(line)
                char_count = 0
            else:
                char_count += len(line)
                if char_count <= 400:
                    trimmed.append(line)
                elif char_count - len(line) < 400:
                    trimmed.append(line[:400 - (char_count - len(line))] + "...")
        result = "\n".join(trimmed)

    print(result)
    print()


if __name__ == "__main__":
    main()
