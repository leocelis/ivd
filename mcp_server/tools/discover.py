# mcp_server/tools/discover.py

"""Tools: ivd_find_artifacts, ivd_check_placement, ivd_list_features, ivd_assess_coverage."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
from termcolor import colored

from mcp_server.tools._paths import project_root

LOG = "IVD Tools"


def find_artifacts_tool(scope: str = "all", project_root_arg: Optional[str] = None) -> str:
    """Discover IVD intent artifacts in a repo."""
    print(colored(f"[{LOG}] ivd_find_artifacts: scope={scope}", "cyan"))

    try:
        root = project_root(project_root_arg)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e), "hint": "Pass project_root for your repo."}, indent=2)

    search_patterns = {
        "all": ["**/*_intent.yaml"],
        "system": ["*_system_intent.yaml"],
        "workflow": ["workflows/*_intent.yaml"],
        "module": ["**/*_intent.yaml"],
        "task": ["**/intents/*_intent.yaml"],
    }

    if scope not in search_patterns:
        return json.dumps({"error": f"Invalid scope '{scope}'", "valid_scopes": list(search_patterns.keys())}, indent=2)

    seen = set()
    artifacts = []

    for pattern in search_patterns[scope]:
        for fp in root.glob(pattern):
            if "templates" in str(fp) or "mcp_server" in str(fp):
                continue
            try:
                rel = fp.relative_to(root)
            except ValueError:
                continue

            key = str(rel)
            if key in seen:
                continue
            seen.add(key)

            if "intents/" in key:
                level = "task"
            elif key.startswith("workflows/"):
                level = "workflow"
            elif "_system_intent" in fp.stem:
                level = "system"
            else:
                level = "module"

            if scope == "module" and level in ("task", "workflow", "system"):
                continue

            artifacts.append({
                "path": key,
                "name": fp.stem.replace("_intent", "").replace("_system_intent", ""),
                "level": level,
                "size_bytes": fp.stat().st_size,
            })

    result = {"scope": scope, "count": len(artifacts), "artifacts": artifacts, "search_root": str(root)}
    print(colored(f"[{LOG}] Found {len(artifacts)} artifacts", "green"))
    return json.dumps(result, indent=2)


def check_placement_tool(artifact_path: str, project_root_arg: Optional[str] = None) -> str:
    """Validate that an IVD artifact is in the correct canonical location."""
    print(colored(f"[{LOG}] ivd_check_placement: {artifact_path}", "cyan"))

    root = project_root(project_root_arg, require_exists=False)
    root_exists = root.exists()

    path_input = Path(artifact_path)
    file_path = path_input if path_input.is_absolute() else root / artifact_path
    file_exists = root_exists and file_path.exists()
    path_only_mode = not root_exists

    try:
        rel_path = file_path.relative_to(root)
    except ValueError:
        rel_path = file_path

    path_str = str(rel_path)
    issues = []
    recommendations = []

    if "intents/" in path_str:
        detected_level = "task"
    elif path_str.startswith("workflows/"):
        detected_level = "workflow"
    elif "_system_intent" in file_path.stem:
        detected_level = "system"
        if len(rel_path.parts) > 1:
            issues.append("System-level intent should be at repository root")
    else:
        detected_level = "module"
        if file_exists:
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and isinstance(data.get("scope"), dict) and data["scope"].get("level") == "workflow":
                    detected_level = "workflow"
                    recommendations.append("Workflow intent alongside coordinator (valid alternative).")
            except Exception:
                pass

    if not file_path.stem.endswith("_intent") and "_system_intent" not in file_path.stem:
        issues.append("File name should end with '_intent.yaml' or '_system_intent.yaml'")

    correct = len(issues) == 0
    result = {
        "path": path_str,
        "detected_level": detected_level,
        "placement_correct": correct,
        "validation_mode": "path_only" if path_only_mode else "full",
        "issues": issues,
        "recommendations": recommendations or (
            ["Placement follows IVD conventions"] if correct else
            [f"Review framework.md '{detected_level.title()}-Level Intents' section"]
        ),
    }

    color = "green" if correct else "yellow"
    print(colored(f"[{LOG}] Placement {'correct' if correct else f'{len(issues)} issues'}", color))
    return json.dumps(result, indent=2)


def list_features_tool(
    root_dir: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    project_root_arg: Optional[str] = None,
) -> str:
    """Derive feature inventory from IVD intent artifacts."""
    print(colored(f"[{LOG}] ivd_list_features", "cyan"))

    try:
        root = project_root(project_root_arg)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e)}, indent=2)

    search_root = root / root_dir if root_dir else root
    if not search_root.exists():
        return json.dumps({"error": f"Root not found: {search_root}"}, indent=2)

    features = []
    for pattern in ["**/*_intent.yaml", "**/*_system_intent.yaml"]:
        for fp in search_root.glob(pattern):
            if "templates" in str(fp) or "mcp_server" in str(fp):
                continue
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                features.append({"path": str(fp), "parse_error": str(e)})
                continue

            if not data:
                continue

            meta = data.get("metadata") or {}
            intent_block = data.get("intent") or {}
            summary = intent_block.get("summary") if isinstance(intent_block, dict) else None

            feature_id = meta.get("feature_id") or fp.stem.replace("_system_intent", "").replace("_intent", "")
            feat_category = meta.get("category")
            feat_status = meta.get("status")

            if category and feat_category != category:
                continue
            if status and feat_status != status:
                continue

            try:
                rel = fp.relative_to(search_root)
            except ValueError:
                rel = fp

            features.append({
                "path": str(rel),
                "feature_id": feature_id,
                "summary": summary,
                "category": feat_category,
                "tags": meta.get("tags") or [],
                "status": feat_status,
            })

    result = {
        "search_root": str(search_root),
        "count": len(features),
        "filters_applied": {"category": category, "status": status},
        "features": features,
    }

    print(colored(f"[{LOG}] Listed {len(features)} features", "green"))
    return json.dumps(result, indent=2)


# =========================================================================
# Coverage Assessment
# =========================================================================

# Directories that are typically not coverable modules
_SKIP_DIRS: Set[str] = {
    ".git", ".github", ".vscode", ".cursor", ".ivd",
    "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache",
    "venv", ".venv", "env", ".env",
    "dist", "build", "target", "out",
    "templates", "examples", "docs",
    "brain", "knowledge",  # MCP server internal
}

# Extensions that signal "this directory has implementation code"
_CODE_EXTENSIONS: Set[str] = {
    ".py", ".ts", ".js", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".kt", ".rb",
    ".cs", ".cpp", ".c", ".swift",
}


def _is_coverable_dir(d: Path, root: Path) -> bool:
    """Return True if directory looks like a module that could have intent."""
    name = d.name
    if name.startswith(".") or name.startswith("_"):
        return False
    if name in _SKIP_DIRS:
        return False
    # Must contain at least one code file (not just configs/docs)
    for ext in _CODE_EXTENSIONS:
        if list(d.glob(f"*{ext}")):
            return True
    return False


def _find_coverable_modules(root: Path, depth: str) -> List[Dict]:
    """
    Walk project and find directories that look like coverable modules.

    depth controls scan depth:
      - "module": top-level and one level of nesting (e.g. agent/lead_scorer/)
      - "full": also includes task-level detection inside modules
    """
    modules: List[Dict] = []
    seen_paths: Set[str] = set()

    # Walk first two levels of directories for module candidates
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not _is_coverable_dir(child, root):
            continue

        rel = str(child.relative_to(root))
        if rel not in seen_paths:
            seen_paths.add(rel)
            modules.append({"path": rel, "type": "top-level"})

        # One level deeper (e.g. agent/lead_scorer/)
        for sub in sorted(child.iterdir()):
            if not sub.is_dir():
                continue
            if not _is_coverable_dir(sub, root):
                continue
            sub_rel = str(sub.relative_to(root))
            if sub_rel not in seen_paths:
                seen_paths.add(sub_rel)
                modules.append({"path": sub_rel, "type": "nested"})

    return modules


def _find_workflow_dirs(root: Path) -> List[str]:
    """Find directories that look like workflow containers."""
    results = []
    wf_dir = root / "workflows"
    if wf_dir.is_dir():
        results.append("workflows")
    # Also check for coordinator files that might indicate workflows
    for pattern in ["**/coordinator*.py", "**/orchestrat*.py"]:
        for fp in root.glob(pattern):
            rel_dir = str(fp.parent.relative_to(root))
            if rel_dir not in results and rel_dir != ".":
                results.append(rel_dir)
    return results


def _code_file_count(d: Path) -> int:
    """Count code files in a directory (non-recursive)."""
    count = 0
    for ext in _CODE_EXTENSIONS:
        count += len(list(d.glob(f"*{ext}")))
    return count


def _priority_hint(module_path: str, code_count: int) -> str:
    """Heuristic priority hint for uncovered modules."""
    path_lower = module_path.lower()
    # High priority keywords
    high_keywords = ["api", "auth", "core", "agent", "service", "workflow", "payment", "order"]
    for kw in high_keywords:
        if kw in path_lower:
            return "high"
    if code_count >= 5:
        return "high"
    if code_count >= 3:
        return "medium"
    return "low"


def assess_coverage_tool(
    project_root_arg: Optional[str] = None,
    depth: str = "module",
    include_suggestions: bool = True,
) -> str:
    """
    Assess intent coverage across a project.

    Scans project structure (directories, modules) and compares against
    existing *_intent.yaml artifacts. Returns a structured coverage report
    that the AI agent can interpret and use to recommend where to add intents.

    Args:
        project_root_arg: Path to repo root.
        depth: "module" (system + modules) or "full" (system + workflow + module + task).
        include_suggestions: Whether to include prioritized recommendations.
    """
    print(colored(f"[{LOG}] ivd_assess_coverage: depth={depth}", "cyan"))

    try:
        root = project_root(project_root_arg)
    except FileNotFoundError as e:
        return json.dumps({"error": str(e), "hint": "Pass project_root for your repo."}, indent=2)

    # --- 1. System-level coverage ---
    system_intents = list(root.glob("*_system_intent.yaml")) + list(root.glob("system_intent.yaml"))
    has_system_intent = len(system_intents) > 0
    system_files = [str(f.relative_to(root)) for f in system_intents]

    # --- 2. Discover existing intents ---
    existing_intents: Dict[str, Dict] = {}  # rel_path → info
    for fp in root.rglob("*_intent.yaml"):
        if "templates" in str(fp) or "mcp_server" in str(fp):
            continue
        try:
            rel = str(fp.relative_to(root))
        except ValueError:
            continue

        # Determine level
        if "intents/" in rel:
            level = "task"
        elif rel.startswith("workflows/"):
            level = "workflow"
        elif "_system_intent" in fp.stem:
            level = "system"
        else:
            level = "module"

        # Determine which directory this intent covers
        covered_dir = str(fp.parent.relative_to(root))
        if level == "task":
            # task intents are in {module}/intents/ → covers parent
            covered_dir = str(fp.parent.parent.relative_to(root))

        existing_intents[rel] = {
            "level": level,
            "covers_dir": covered_dir,
            "name": fp.stem.replace("_intent", "").replace("_system_intent", ""),
        }

    # Set of directories covered by module-level intents
    covered_dirs: Set[str] = set()
    for info in existing_intents.values():
        if info["level"] in ("module", "task"):
            covered_dirs.add(info["covers_dir"])

    # --- 3. Find coverable modules ---
    coverable = _find_coverable_modules(root, depth)

    covered_modules = []
    uncovered_modules = []

    for mod in coverable:
        mod_path = mod["path"]
        if mod_path in covered_dirs:
            # Find which intents cover it
            covering = [
                path for path, info in existing_intents.items()
                if info["covers_dir"] == mod_path
            ]
            covered_modules.append({
                "path": mod_path,
                "intents": covering,
            })
        else:
            entry = {"path": mod_path}
            if include_suggestions:
                code_count = _code_file_count(root / mod_path)
                entry["code_files"] = code_count
                entry["priority"] = _priority_hint(mod_path, code_count)
            uncovered_modules.append(entry)

    # --- 4. Workflow coverage (depth=full) ---
    workflow_coverage = None
    if depth == "full":
        workflow_dirs = _find_workflow_dirs(root)
        workflow_intents = [
            path for path, info in existing_intents.items()
            if info["level"] == "workflow"
        ]
        workflow_coverage = {
            "workflow_dirs_found": workflow_dirs,
            "workflow_intents": workflow_intents,
            "covered": len(workflow_intents) > 0 or len(workflow_dirs) == 0,
        }

    # --- 5. Calculate summary ---
    total_coverable = len(coverable)
    total_covered = len(covered_modules)
    coverage_pct = round((total_covered / total_coverable * 100), 1) if total_coverable > 0 else 0.0

    # Sort uncovered by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    if include_suggestions:
        uncovered_modules.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))

    # --- 6. Build result ---
    result = {
        "summary": {
            "project_root": str(root),
            "depth": depth,
            "has_system_intent": has_system_intent,
            "system_intent_files": system_files,
            "total_coverable_modules": total_coverable,
            "covered_modules": total_covered,
            "uncovered_modules": total_coverable - total_covered,
            "coverage_percent": coverage_pct,
            "total_intent_artifacts": len(existing_intents),
        },
        "covered": covered_modules,
        "uncovered": uncovered_modules,
    }

    if workflow_coverage is not None:
        result["workflow_coverage"] = workflow_coverage

    if include_suggestions:
        suggestions = []
        if not has_system_intent:
            suggestions.append({
                "action": "Run ivd_init to create system_intent.yaml",
                "reason": "No system-level intent found. System intent captures project conventions and serves as parent for all other intents.",
                "priority": "high",
            })
        high_priority = [m for m in uncovered_modules if m.get("priority") == "high"]
        if high_priority:
            suggestions.append({
                "action": f"Create module-level intents for {len(high_priority)} high-priority module(s)",
                "modules": [m["path"] for m in high_priority],
                "reason": "These modules contain significant code and/or are in critical paths (API, auth, agents, services).",
                "priority": "high",
            })
        if depth != "full" and total_coverable > 0:
            suggestions.append({
                "action": "Run with depth='full' for workflow and task-level analysis",
                "reason": "Module-level coverage assessed. Full depth also checks workflow and task-level gaps.",
                "priority": "low",
            })
        result["suggestions"] = suggestions

    color = "green" if coverage_pct >= 50 else ("yellow" if coverage_pct >= 20 else "red")
    print(colored(f"[{LOG}] Coverage: {coverage_pct}% ({total_covered}/{total_coverable} modules)", color))
    return json.dumps(result, indent=2)
