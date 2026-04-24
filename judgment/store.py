# ivd/judgment/store.py

"""
Judgment engine — filesystem persistence for ``.judgment/`` artifacts.

The Judgment phase keeps everything on disk so a ``ls .judgment/ledger/`` is
literally the state of the system. The Store class is the only abstraction
that touches the filesystem; tools and other engine modules go through it.

Layout (laid down by ``ivd_judgment_init``):

    <project_root>/.judgment/
      config.yaml
      baselines/<domain>_baseline.yaml
      ledger/{raw,codified,paired,resolved,archived}/<entry>.yaml
      patterns/<pattern>.yaml
      recommendations/<recommendation>.yaml

Reference:
  ivd/judgment_layer.md §2.1 (folder layout),
                       §3 (state machine + on-disk moves).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from judgment.schema import (
    Baseline,
    DEFAULT_HALF_LIFE_DAYS,
    DomainDepth,
    LedgerEntry,
    Pattern,
)

JUDGMENT_DIRNAME = ".judgment"
JUDGMENT_SUBDIRS = (
    "baselines",
    "ledger/raw",
    "ledger/codified",
    "ledger/paired",
    "ledger/resolved",
    "ledger/archived",
    "patterns",
    "recommendations",
)
LEDGER_STATES = ("raw", "codified", "paired", "resolved", "archived")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_len: int = 40) -> str:
    """Lowercase, collapse non-alphanum runs to '-', trim leading/trailing dashes."""
    if not text:
        return "entry"
    slug = _SLUG_RE.sub("-", text.strip().lower()).strip("-")
    return (slug[:max_len] or "entry").strip("-")


def read_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Read a YAML file. Returns None on missing or parse failure."""
    if not path.is_file():
        return None
    try:
        return yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None


def write_yaml(path: Path, payload: Dict[str, Any]) -> None:
    """Write a YAML file atomically (creates parent dirs)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


class JudgmentStore:
    """Filesystem-backed accessor for a single ``.judgment/`` folder.

    Construct one of these per project root; the constructor does NOT enforce
    the activation gate (that's ``is_active``). All write paths assume the
    activation gate has already been checked by the caller.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.root = project_root / JUDGMENT_DIRNAME

    # ----- Activation gate ----------------------------------------------

    def is_active(self) -> bool:
        try:
            return self.root.is_dir()
        except Exception:
            return False

    # ----- Directory bootstrap ------------------------------------------

    def ensure_dirs(self) -> Tuple[List[str], List[str]]:
        """Create the canonical subdir layout. Returns (created, already_present)."""
        created: List[str] = []
        already: List[str] = []

        if self.root.exists():
            already.append(JUDGMENT_DIRNAME + "/")
        else:
            self.root.mkdir(parents=True, exist_ok=True)
            created.append(JUDGMENT_DIRNAME + "/")

        for sub in JUDGMENT_SUBDIRS:
            target = self.root / sub
            if target.exists():
                already.append(f"{JUDGMENT_DIRNAME}/{sub}/")
            else:
                target.mkdir(parents=True, exist_ok=True)
                created.append(f"{JUDGMENT_DIRNAME}/{sub}/")

        return created, already

    # ----- Path resolution ----------------------------------------------

    def ledger_path(self, state: str, entry_id: str) -> Path:
        return self.root / "ledger" / state / f"{entry_id}.yaml"

    def baseline_path(self, domain: str) -> Path:
        return self.root / "baselines" / f"{slugify(domain)}_baseline.yaml"

    def pattern_path(self, pattern_id: str) -> Path:
        return self.root / "patterns" / f"{pattern_id}.yaml"

    def recommendation_path(self, rec_id: str) -> Path:
        return self.root / "recommendations" / f"{rec_id}.yaml"

    def config_path(self) -> Path:
        return self.root / "config.yaml"

    # ----- Iteration ----------------------------------------------------

    def iter_ledger(self, *states: str) -> List[Tuple[str, Path, Dict[str, Any]]]:
        """Yield ``(state, path, raw_payload)`` for ledger entries in ``states``.

        Returns the *raw* dict so callers that don't care about typed entries
        skip the dataclass round-trip cost.
        """
        states = states or LEDGER_STATES
        out: List[Tuple[str, Path, Dict[str, Any]]] = []
        for st in states:
            sub = self.root / "ledger" / st
            if not sub.is_dir():
                continue
            for fp in sorted(sub.glob("*.yaml")):
                payload = read_yaml(fp)
                if payload:
                    out.append((st, fp, payload))
        return out

    def iter_ledger_typed(self, *states: str) -> List[Tuple[str, Path, LedgerEntry]]:
        """Same as ``iter_ledger`` but materializes a typed ``LedgerEntry``."""
        return [
            (state, fp, LedgerEntry.from_dict(payload))
            for state, fp, payload in self.iter_ledger(*states)
        ]

    def iter_patterns(self) -> List[Tuple[Path, Pattern]]:
        out: List[Tuple[Path, Pattern]] = []
        pdir = self.root / "patterns"
        if not pdir.is_dir():
            return out
        for fp in sorted(pdir.glob("*.yaml")):
            data = read_yaml(fp)
            if data:
                out.append((fp, Pattern.from_dict(data)))
        return out

    # ----- Baselines ----------------------------------------------------

    def baseline(self, domain: str) -> Optional[Baseline]:
        if not domain:
            return None
        data = read_yaml(self.baseline_path(domain))
        if not data:
            return None
        return Baseline.from_dict(data)

    def baseline_raw(self, domain: str) -> Optional[Dict[str, Any]]:
        if not domain:
            return None
        return read_yaml(self.baseline_path(domain))

    def half_life_for(self, domain: str) -> int:
        bl = self.baseline(domain)
        return bl.half_life_days() if bl else DEFAULT_HALF_LIFE_DAYS

    # ----- Depth resolution ---------------------------------------------

    @staticmethod
    def depth_for_entry(
        entry: Dict[str, Any], baseline: Optional[Dict[str, Any]]
    ) -> str:
        """Resolve the leo_domain_depth for an entry, falling back to the baseline.

        Order:  entry.leo_domain_depth → baseline.leo_domain_depth → 'practitioner'.
        """
        from judgment.schema import DEPTH_WEIGHT  # local to avoid cycle

        depth = entry.get("leo_domain_depth")
        if depth in DEPTH_WEIGHT:
            return depth
        if baseline and baseline.get("leo_domain_depth") in DEPTH_WEIGHT:
            return baseline["leo_domain_depth"]
        return DomainDepth.PRACTITIONER.value

    # ----- Ledger writes ------------------------------------------------

    def write_entry(self, entry: LedgerEntry, state: Optional[str] = None) -> Path:
        """Persist a ledger entry under the given (or its current) state."""
        target = self.ledger_path(state or entry.state, entry.id)
        write_yaml(target, entry.to_dict())
        return target

    def move_entry(self, entry_id: str, from_state: str, to_state: str) -> Path:
        """Move a ledger entry on disk: read → write to new path → unlink old."""
        from_path = self.ledger_path(from_state, entry_id)
        if not from_path.exists():
            raise FileNotFoundError(
                f"Cannot move entry: {from_path} does not exist"
            )
        payload = read_yaml(from_path) or {}
        payload["state"] = to_state
        to_path = self.ledger_path(to_state, entry_id)
        write_yaml(to_path, payload)
        from_path.unlink(missing_ok=True)
        return to_path

    # ----- Patterns -----------------------------------------------------

    def write_pattern(self, pattern: Pattern) -> Path:
        """Persist a Pattern (stamping engine_version + detection_hash on the way)."""
        pattern.stamp_hash()
        target = self.pattern_path(pattern.id)
        write_yaml(target, pattern.to_dict())
        return target

    def read_pattern(self, pattern_id: str) -> Optional[Pattern]:
        data = read_yaml(self.pattern_path(pattern_id))
        if not data:
            return None
        return Pattern.from_dict(data)

    # ----- Convenience --------------------------------------------------

    def next_unique_path(self, base_path: Path) -> Tuple[Path, str]:
        """Append ``_2``, ``_3``, … to ``base_path.stem`` until the file does not exist."""
        if not base_path.exists():
            return base_path, base_path.stem
        suffix = 1
        while True:
            suffix += 1
            candidate = base_path.with_name(f"{base_path.stem}_{suffix}{base_path.suffix}")
            if not candidate.exists():
                return candidate, candidate.stem
