"""University SQL Quiz: a Streamlit app.

Sign in with Supabase Auth, pick a question, write SQL, run it against the
live Supabase Postgres database, and save your answer.
"""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

import quiz_db
from questions import QUESTIONS, TOTAL_POINTS

st.set_page_config(page_title="University SQL Quiz", page_icon="🎓", layout="wide")
load_dotenv()  # reads .env on your laptop; on Streamlit Cloud the secrets are used instead


def setting(name):
    """Read a setting from Streamlit secrets (deployed) or environment / .env (local)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name)


DATABASE_URL = setting("DATABASE_URL")
SUPABASE_URL = setting("SUPABASE_URL")
SUPABASE_KEY = setting("SUPABASE_KEY")

if not (DATABASE_URL and SUPABASE_URL and SUPABASE_KEY):
    st.error("Missing settings. Set DATABASE_URL, SUPABASE_URL and SUPABASE_KEY (see README).")
    st.stop()

# One Supabase client per browser session, so users never share a login.
if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
if "user" not in st.session_state:
    st.session_state.user = None

sb = st.session_state.supabase
user = st.session_state.user
signed_in = user is not None

# ---------------- Sidebar: sign in / sign up ----------------
with st.sidebar:
    st.header("Account")
    if signed_in:
        st.success(f"Signed in as **{user['email']}**")
        if st.button("Sign out"):
            try:
                sb.auth.sign_out()
            except Exception:
                pass
            st.session_state.user = None
            st.rerun()
    else:
        tab_in, tab_up = st.tabs(["Sign in", "Sign up"])
        new_user = None

        with tab_in:
            with st.form("sign_in"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in"):
                    try:
                        res = sb.auth.sign_in_with_password({"email": email, "password": password})
                        new_user = res.user
                    except Exception as e:
                        st.error(f"Sign-in failed: {e}")

        with tab_up:
            with st.form("sign_up"):
                email = st.text_input("Email", key="up_email")
                password = st.text_input("Password (6+ characters)", type="password", key="up_pw")
                if st.form_submit_button("Create account"):
                    try:
                        res = sb.auth.sign_up({"email": email, "password": password})
                        if res.session is not None:
                            new_user = res.user
                        else:
                            st.info("Account created. Check your email to confirm, then sign in.")
                    except Exception as e:
                        st.error(f"Sign-up failed: {e}")

        if new_user is not None:
            st.session_state.user = {"id": str(new_user.id), "email": new_user.email}
            st.rerun()

    st.divider()
    st.caption("Signed-out visitors can read the questions, but only signed-in users can run or save SQL.")

# ---------------- Main page ----------------
st.title("🎓 University SQL Quiz")
st.write(
    f"**{len(QUESTIONS)} questions · {TOTAL_POINTS} points.** "
    "Write a SQL query for each question and run it against the live database. "
    "Answers are graded on the result set, not on matching the SQL exactly."
)

with st.expander("📋 Database tables"):
    st.markdown(
        """
| Table | Columns |
|---|---|
| **universities** (18 rows) | `id`, `name`, `state`, `type` ('Public'/'Private'), `founded`, `enrollment` |
| **programs** (34 rows) | `id`, `university_id` → universities.id, `program_name`, `degree` ('MS'/'MBA'), `annual_tuition` |
| **admissions** (36 rows) | `id`, `university_id` → universities.id, `year` (2024/2025), `applicants`, `admitted` |
"""
    )

if not signed_in:
    st.info("🔒 Sign in from the sidebar to run and save queries.")

labels = [f"Q{q['id']} · {q['title']} ({q['points']} pts)" for q in QUESTIONS]
choice = st.selectbox("Choose a question", labels)
q = QUESTIONS[labels.index(choice)]

st.subheader(f"Q{q['id']}. {q['title']}")
st.caption(f"{q['level']} · {q['points']} points")
st.markdown(q["prompt"])

with st.expander("💡 Hint: expected SQL and expected result"):
    st.code(q["sql"], language="sql")
    st.dataframe(
        pd.DataFrame(q["expected_rows"], columns=q["expected_columns"]),
        hide_index=True,
    )

sql_text = st.text_area(
    "Your SQL",
    key=f"sql_{q['id']}",
    height=200,
    placeholder="SELECT ...",
    disabled=not signed_in,
)

col_run, col_save, _ = st.columns([1, 1, 4])
run_clicked = col_run.button("▶ Run", type="primary", disabled=not signed_in)
save_clicked = col_save.button("💾 Save answer", disabled=not signed_in)

if run_clicked or save_clicked:
    # Server-side gate: even if a button were somehow clicked, signed-out users stop here.
    if not signed_in:
        st.error("You must be signed in to run or save SQL.")
        st.stop()
    if not sql_text.strip():
        st.warning("Write a query first.")
        st.stop()

if run_clicked:
    succeeded = False
    try:
        columns, rows, truncated = quiz_db.run_quiz_query(DATABASE_URL, sql_text)
        succeeded = True
        st.markdown("**Result**")
        st.dataframe(pd.DataFrame(rows, columns=columns), hide_index=True)
        st.caption(f"{len(rows)} row(s)" + (" (showing the first 500)" if truncated else ""))

        verdict = quiz_db.compare(rows, q["expected_rows"])
        if verdict == "match":
            st.success("✅ Matches the expected result.")
        elif verdict == "wrong_order":
            st.warning("Right rows, but in a different order. Check your ORDER BY.")
        else:
            st.info("This doesn't match the expected result yet. Compare with the hint.")
    except quiz_db.QueryRejected as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Query error: {e}")
    finally:
        try:
            quiz_db.log_event(DATABASE_URL, user["email"], "run", q["id"], sql_text, succeeded)
        except Exception:
            pass

if save_clicked:
    try:
        quiz_db.save_answer(DATABASE_URL, user["id"], user["email"], q["id"], sql_text)
        quiz_db.log_event(DATABASE_URL, user["email"], "save", q["id"], sql_text, True)
        st.success(f"Saved your answer to Q{q['id']}.")
    except Exception as e:
        st.error(f"Could not save: {e}")

if signed_in:
    with st.expander("📁 My saved answers"):
        try:
            saved = quiz_db.get_saved_answers(DATABASE_URL, user["id"])
            if saved:
                st.dataframe(
                    pd.DataFrame(saved, columns=["question", "sql", "saved_at"]),
                    hide_index=True,
                )
            else:
                st.write("No saved answers yet.")
        except Exception as e:
            st.error(f"Could not load saved answers: {e}")
