# examples/intent_demo/correct_export.py
#
# Implementation written against examples/intent_demo/csv_export_intent.yaml.
# Every line here traces to one of the three constraints in that file.

import csv
import io


def export_users_csv(requesting_user, users):
    """Export users to CSV. Constraint: admin_only."""
    if requesting_user.get("role") != "admin":
        raise PermissionError("Only admin users may generate this export")

    output = io.StringIO()
    writer = csv.writer(output)
    # Constraint: column_schema — exact header, exact order.
    writer.writerow(["user_id", "email", "created_at", "last_login", "status"])
    for u in users:
        writer.writerow([
            u["user_id"],
            u["email"],
            # Constraint: iso_dates.
            u["created_at"].isoformat(timespec="seconds"),
            u["last_login"].isoformat(timespec="seconds"),
            u["status"],
        ])
    return output.getvalue()
