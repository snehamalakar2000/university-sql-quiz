"""All database access for the quiz app.

- Quiz queries run inside a READ ONLY transaction, as the restricted `quiz_taker` role,
  with a 5-second timeout, so a taker can only read the 3 quiz tables.
- Saving answers and writing the audit log use parameterized queries (%s placeholders),
  never f-strings, so user input cannot inject SQL.
"""

import re
from decimal import Decimal

MAX_ROWS = 500
BLOCKED_WORDS = re.compile(r"\b(set_config|pg_sleep|dblink|lo_import|lo_export)\b", re.IGNORECASE)


class QueryRejected(Exception):
    """Raised when a quiz query is not allowed (before it reaches the database)."""


def _connect(database_url):
    import psycopg  # imported here so questions/compare logic can be used without it

    return psycopg.connect(database_url, connect_timeout=10, prepare_threshold=None)


def check_query(sql_text):
    """Allow a single SELECT (or WITH ... SELECT) statement only."""
    query = sql_text.strip().rstrip(";").strip()
    if not query:
        raise QueryRejected("Write a query first.")
    if ";" in query:
        raise QueryRejected("Run one statement at a time (only a single ; at the end is allowed).")
    first_word = query.split(None, 1)[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise QueryRejected("Only SELECT queries (or WITH ... SELECT) are allowed in this quiz.")
    if BLOCKED_WORDS.search(query):
        raise QueryRejected("That function is not allowed in this quiz.")
    return query


def run_quiz_query(database_url, sql_text):
    """Run a taker's query safely. Returns (column_names, rows, truncated)."""
    query = check_query(sql_text)
    with _connect(database_url) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SET LOCAL statement_timeout = '5s'")
                cur.execute("SET LOCAL ROLE quiz_taker")
                cur.execute(query)
                if cur.description is None:
                    return [], [], False
                columns = [col.name for col in cur.description]
                rows = cur.fetchmany(MAX_ROWS + 1)
        finally:
            conn.rollback()  # nothing a quiz query does is ever kept
    return columns, rows[:MAX_ROWS], len(rows) > MAX_ROWS


def save_answer(database_url, user_id, user_email, question_id, sql_text):
    with _connect(database_url) as conn:
        conn.execute(
            "INSERT INTO saved_answers (user_id, user_email, question_id, sql_text) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, user_email, question_id, sql_text),
        )


def log_event(database_url, user_email, action, question_id, sql_text, succeeded):
    """Append one row to the audit log (who ran or saved what, and when)."""
    with _connect(database_url) as conn:
        conn.execute(
            "INSERT INTO audit_log (user_email, action, question_id, sql_text, succeeded) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_email, action, question_id, sql_text, succeeded),
        )


def get_saved_answers(database_url, user_id):
    with _connect(database_url) as conn:
        cur = conn.execute(
            "SELECT question_id, sql_text, saved_at FROM saved_answers "
            "WHERE user_id = %s ORDER BY saved_at DESC",
            (user_id,),
        )
        return cur.fetchall()


# ---------- comparing a result with the expected result ----------

def _normalize(value):
    """Make 3.6, Decimal('3.6') and '3.6' compare equal; trim text."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float, Decimal)):
        return round(float(value), 6)
    text = str(value).strip()
    try:
        return round(float(text), 6)
    except ValueError:
        return text


def compare(actual_rows, expected_rows):
    """Returns 'match', 'wrong_order', or 'no_match'. Column names are ignored."""
    actual = [tuple(_normalize(v) for v in row) for row in actual_rows]
    expected = [tuple(_normalize(v) for v in row) for row in expected_rows]
    if actual == expected:
        return "match"
    if sorted(actual, key=repr) == sorted(expected, key=repr):
        return "wrong_order"
    return "no_match"
