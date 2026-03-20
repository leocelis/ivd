# mcp_server/tools/_paths.py

"""
Shared path resolution for IVD tools.

IVD repo structure:
    ivd/                    ← framework root (docs, recipes, templates, etc.)
    ivd/mcp_server/         ← server code
    ivd/mcp_server/tools/   ← this directory
"""

from pathlib import Path
from typing import Optional

# Framework root: up from tools/ → mcp_server/ → ivd/
IVD_FRAMEWORK_ROOT = Path(__file__).parent.parent.parent


def get_framework_path() -> Path:
    """Get path to IVD framework root (repo root)."""
    if not IVD_FRAMEWORK_ROOT.exists():
        raise FileNotFoundError(f"IVD framework not found at {IVD_FRAMEWORK_ROOT}")
    return IVD_FRAMEWORK_ROOT


def project_root(project_root_arg: Optional[str] = None, *, require_exists: bool = True) -> Path:
    """
    Resolve project root for tools that operate on user projects.

    Args:
        project_root_arg: Optional path to repo root. When None, defaults to IVD repo root.
        require_exists: If True, raise FileNotFoundError when path doesn't exist.
    """
    if project_root_arg:
        root = Path(project_root_arg).resolve()
        if require_exists and not root.exists():
            raise FileNotFoundError(f"Project root not found: {root}")
        return root
    return IVD_FRAMEWORK_ROOT
