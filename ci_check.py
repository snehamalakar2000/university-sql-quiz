"""Database check run by GitHub Actions.

Connects to Supabase using the DATABASE_URL GitHub Secret and checks that:
1. The 3 quiz tables exist and have the expected number of rows.
2. Every question's hint SQL returns its expected result (run as the quiz_taker role).
3. The quiz_taker role cannot read the audit log (integrity check).
"""

import os
import sys

import quiz_db
from questions import QUESTIONS

EXPECTED_COUNTS = {"universities": 18, "programs": 34, "admissions": 36}

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    sys.exit("DATABASE_URL is not set. Add it as a GitHub Secret.")

failures = 0

# 1. Row counts
with quiz_db._connect(database_url) as conn:
    for table, expected in EXPECTED_COUNTS.items():
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # fixed table names, not user input
        ok = count == expected
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {table}: {count} rows (expected {expected})")

# 2. Every hint returns its expected result
for q in QUESTIONS:
    _, rows, _ = quiz_db.run_quiz_query(database_url, q["sql"])
    verdict = quiz_db.compare(rows, q["expected_rows"])
    ok = verdict == "match"
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  Q{q['id']} hint result: {verdict}")

# 3. quiz_taker must NOT be able to read the audit log
try:
    quiz_db.run_quiz_query(database_url, "SELECT * FROM audit_log")
    print("FAIL  quiz_taker could read audit_log")
    failures += 1
except Exception:
    print("PASS  quiz_taker cannot read audit_log")

if failures:
    sys.exit(f"{failures} check(s) failed")
print("All checks passed.")
