# ivd/judgment/freshness.py

"""
Judgment engine — pattern freshness math.

A pattern's freshness is a monotonic function of the time since the last
ledger entry joined it, scaled by the domain baseline's ``half_life_days``:

  age <=     half_life       → fresh
  age <= 2 * half_life       → aging
  age <= 3 * half_life       → stale
  else                       → expired

Freshness gates injection (expired patterns are not injected) and
recommendation (expired patterns cannot be promoted).

Reference:
  ivd/judgment_layer.md §3.6 (pattern freshness),
                       §4.2 (injection gating).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from judgment.schema import DEFAULT_HALF_LIFE_DAYS, Freshness


def age_days(iso_ts: Optional[str]) -> Optional[float]:
    """Days since ``iso_ts`` (UTC). Accepts ``YYYY-MM-DDTHH:MM:SSZ`` or ``YYYY-MM-DD``."""
    if not iso_ts:
        return None
    # Try the full ISO-with-Z first, then the date-only form.
    try:
        ts = datetime.strptime(iso_ts.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            ts = datetime.strptime(iso_ts, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0


def freshness_for(age: Optional[float], half_life_days: int = DEFAULT_HALF_LIFE_DAYS) -> str:
    """Map (age_days, half_life_days) → freshness string.

    ``age=None`` collapses to ``fresh`` (no age data ⇒ assume just-emitted).
    """
    if age is None:
        return Freshness.FRESH.value
    if age <= half_life_days:
        return Freshness.FRESH.value
    if age <= 2 * half_life_days:
        return Freshness.AGING.value
    if age <= 3 * half_life_days:
        return Freshness.STALE.value
    return Freshness.EXPIRED.value
