# examples/intent_demo/test_csv_export.py
#
# Real pytest tests, one per constraint in csv_export_intent.yaml. Which
# implementation they run against is controlled by the INTENT_DEMO_IMPL
# env var (set by run_demo.py) so the same test file proves both halves of
# the demo: fails against hallucinated_export.py, passes against
# correct_export.py.

import importlib
import os
import re
from datetime import datetime

import pytest

IMPL_MODULE = os.environ.get("INTENT_DEMO_IMPL", "correct_export")
impl = importlib.import_module(IMPL_MODULE)
export_users_csv = impl.export_users_csv

ADMIN = {"user_id": "u_admin", "role": "admin"}
NON_ADMIN = {"user_id": "u_1", "role": "member"}

USERS = [
    {
        "user_id": "u_100",
        "email": "ada@example.com",
        "full_name": "Ada Lovelace",
        "created_at": datetime(2026, 1, 15, 9, 30, 0),
        "last_login": datetime(2026, 7, 10, 14, 5, 0),
        "status": "active",
    }
]


def test_admin_required():
    """constraint: admin_only"""
    with pytest.raises(PermissionError):
        export_users_csv(NON_ADMIN, USERS)


def test_column_schema():
    """constraint: column_schema"""
    csv_text = export_users_csv(ADMIN, USERS)
    header = csv_text.splitlines()[0]
    assert header == "user_id,email,created_at,last_login,status"


def test_iso_dates():
    """constraint: iso_dates"""
    csv_text = export_users_csv(ADMIN, USERS)
    row = csv_text.splitlines()[1]
    iso_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    dates_found = iso_pattern.findall(row)
    assert len(dates_found) == 2, f"expected 2 ISO 8601 dates in row, found {len(dates_found)}: {row}"
