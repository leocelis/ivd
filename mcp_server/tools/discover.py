# mcp_server/tools/discover.py

"""Tools: ivd_find_artifacts, ivd_check_placement, ivd_list_features."""

import json
from pathlib import Path
from typing import Optional

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
            if "framework/ivd" in str(fp) or "templates" in str(fp) or "mcp_server" in str(fp):
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
            if "framework/ivd" in str(fp) or "templates" in str(fp) or "mcp_server" in str(fp):
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
