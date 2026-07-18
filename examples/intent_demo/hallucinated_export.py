# examples/intent_demo/hallucinated_export.py
#
# This is what a plausible AI response to the vague prompt "Add export to
# CSV for admin compliance reporting" looks like — no structured intent,
# no explicit constraints, just gap-filling from parametric training-data
# patterns. It is internally consistent, readable, and wrong in three
# specific ways that the constraint tests in test_csv_export.py catch.

import csv
import io


def export_users_csv(requesting_user, users):
    """Export users to CSV. (No admin check — the prompt never said who can call this.)"""
    output = io.StringIO()
    # Column choice is a guess: a "typical" user export includes a name field
    # and renames a couple of columns to what a generic user table looks like.
    writer = csv.writer(output)
    writer.writerow(["id", "email", "full_name", "created_at", "last_login_at", "is_active"])
    for u in users:
        writer.writerow([
            u["user_id"],
            u["email"],
            u.get("full_name", ""),
            # US-style date formatting — the most common default in training data.
            u["created_at"].strftime("%m/%d/%Y"),
            u["last_login"].strftime("%m/%d/%Y"),
            u["status"] == "active",
        ])
    return output.getvalue()
