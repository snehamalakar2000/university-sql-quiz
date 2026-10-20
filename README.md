# 🎓 University SQL Quiz

A 20-point SQL quiz that runs against a live, hosted PostgreSQL database. Students sign in, pick a question, write SQL, run it, and see the result table from the real database.

## 🔗 Live quiz

**https://university-sql-quiz-yb6dvadw8x6s4avfhmzkm8.streamlit.app/**

---

## How to use the quiz

1. Open the quiz link above.
2. In the left sidebar, open **Sign up**, enter an email and a password (6+ characters), and click **Create account**. You are signed in right away. (Next time, use **Sign in**.)
3. Choose a question from the **Choose a question** dropdown.
4. Type your SQL in **Your SQL** and click **▶ Run**. The result table appears below, followed by a check:
   - ✅ **Matches the expected result**
   - ⚠️ **Right rows, but in a different order** (check your `ORDER BY`)
   - ℹ️ **Doesn't match the expected result yet**
5. Click **💾 Save answer** to store your SQL. Open **📁 My saved answers** to see everything you saved.
6. Each question has a **💡 Hint** section with the expected SQL and the expected result.

Answers are graded on the **result set**, not on matching the hint SQL character-for-character.

**Signed-out visitors** can read the questions, but the SQL box, **Run**, and **Save** are disabled. The app also re-checks sign-in on the server before running or saving anything.

---

## System overview

```
Browser ──► Streamlit app (Streamlit Community Cloud)
              │
              ├── Supabase Auth ........ sign up / sign in
              │
              └── Supabase PostgreSQL .. quiz data, saved answers, audit log
                    (Session pooler, sslmode=require)

GitHub Actions ──► Supabase PostgreSQL   (reads DATABASE_URL from GitHub Secrets)
```

| Requirement | How it is met |
|---|---|
| **Hosted PostgreSQL** | Supabase project (region us-east-2). The app connects over the network through the **Session pooler** with `sslmode=require`. |
| **Authentication** | **Supabase Auth** (email + password). Signed-out users cannot run or save; signed-in users can do both. |
| **GitHub Actions + Secrets** | `.github/workflows/db-check.yml` runs on every push to `main` (and manually via **Run workflow**). It reads the connection string from the GitHub Secret `DATABASE_URL`. No password is in any file in this repository. |
| **SQL quiz (20 points)** | 5 questions × 4 points, each with a hint (expected SQL + expected result). Signed-in users run SQL against the live database and see the result table. |

---

## The database

Topic: **US universities, their graduate programs, and admissions.** Values are illustrative, not official figures.

| Table | Rows | Columns |
|---|---|---|
| `universities` | 18 | `id` (PK), `name`, `state`, `type` ('Public'/'Private'), `founded`, `enrollment` |
| `programs` | 34 | `id` (PK), `university_id` (FK → universities.id), `program_name`, `degree` ('MS'/'MBA'), `annual_tuition` |
| `admissions` | 36 | `id` (PK), `university_id` (FK → universities.id), `year` (2024/2025), `applicants`, `admitted` |

`universities` is the hub table: `programs` and `admissions` both link to it through `university_id`.

The app also uses two tables of its own:

| Table | Purpose |
|---|---|
| `saved_answers` | Answers saved by signed-in users (user id, email, question, SQL, time) |
| `audit_log` | One row every time someone runs or saves SQL (who, what, when, success) |

---

## The quiz (5 questions, 20 points)

| # | Question | Skill | Points |
|---|---|---|---|
| 1 | Private universities founded before 1850, oldest first | `WHERE`, `ORDER BY` | 4 |
| 2 | States with 3+ universities: count and total enrollment | `GROUP BY`, `HAVING` | 4 |
| 3 | 5 lowest 2025 acceptance rates | `JOIN`, calculation, `LIMIT` | 4 |
| 4 | Universities with 3+ programs | Easy **CTE** | 4 |
| 5 | Top 3 growth in applicants, 2024 → 2025 | Medium **CTE** (two CTEs joined) | 4 |

The full questions, hint SQL, and expected results are in [`questions.py`](questions.py) and in the **💡 Hint** section of each question in the app.

---

## Extra credit

| Item | Implementation |
|---|---|
| **Parameterized queries** | Saving answers and writing the audit log use `%s` placeholders with psycopg (see `quiz_db.py`). No f-string SQL is built from user input. |
| **Audit log** | Every Run and Save writes a row to `audit_log` with the user's email, action, question, SQL, success flag, and timestamp. |
| **Integrity check** | (1) Quiz queries run as a restricted role, `quiz_taker`, which can only `SELECT` from the 3 quiz tables and has **no access** to `audit_log` or `saved_answers`. (2) Triggers make `audit_log` **append-only**: `UPDATE`, `DELETE`, and `TRUNCATE` are rejected for every role. GitHub Actions verifies that `quiz_taker` cannot read the log. |

### How a taker's query is kept safe
- Only a single `SELECT` (or `WITH ... SELECT`) statement is accepted.
- It runs inside a **read-only transaction**, as the `quiz_taker` role, with a **5-second timeout**.
- The transaction is always rolled back, so nothing a quiz query does is kept.

---

## What GitHub Actions checks

`ci_check.py` connects to Supabase with the `DATABASE_URL` secret and checks that:
1. The 3 quiz tables exist with the expected row counts (18, 34, 36).
2. Every question's hint SQL returns exactly its expected result.
3. The `quiz_taker` role cannot read `audit_log`.

See the **Actions** tab for successful runs.

---

## Repository files

| File | Purpose |
|---|---|
| `app.py` | Streamlit app: sign in/up, questions, Run, Save, saved answers |
| `questions.py` | The 5 questions, points, hint SQL, expected results |
| `quiz_db.py` | All database access: safe query runner, save, audit log, result comparison |
| `seed.sql` | Creates and fills the 3 quiz tables |
| `setup_app.sql` | Creates `saved_answers`, `audit_log`, the append-only triggers, the `quiz_taker` role, and RLS |
| `ci_check.py` | Database check run by GitHub Actions |
| `.github/workflows/db-check.yml` | GitHub Actions workflow |
| `requirements.txt` | Python packages |
| `.env.example` | Template for local settings (the real `.env` is git-ignored) |

---

## Set it up yourself

### 1. Supabase
1. Create a project at [supabase.com](https://supabase.com).
2. **SQL Editor** → run `seed.sql`, then run `setup_app.sql`. (If asked about Row Level Security, choose **Run and enable RLS**.)
3. **Authentication → Sign In / Providers** → make sure **Email** is enabled, and turn off **Confirm email** so new accounts can sign in immediately.
4. Collect three values:
   - **DATABASE_URL**: **Connect** → Connection String → Method: **Session pooler**. Replace `[YOUR-PASSWORD]` with your database password and add `?sslmode=require` to the end.
   - **SUPABASE_URL**: Project URL, e.g. `https://<project-ref>.supabase.co`
   - **SUPABASE_KEY**: the anon / publishable key (Project Settings → API Keys)

### 2. Run locally
```bash
git clone https://github.com/snehamalakar2000/university-sql-quiz.git
cd university-sql-quiz
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then fill in the 3 values
streamlit run app.py
```
`.env` is listed in `.gitignore`, so it is never committed.

### 3. GitHub Actions
Repository **Settings → Secrets and variables → Actions → New repository secret**:
- Name: `DATABASE_URL`
- Value: the same Session pooler connection string

Push to `main` (or use **Actions → Database check → Run workflow**).

### 4. Deploy
On [share.streamlit.io](https://share.streamlit.io): **Create app** → this repository, branch `main`, file `app.py`. Under **Advanced settings → Secrets**, add:
```toml
DATABASE_URL = "postgresql://...?sslmode=require"
SUPABASE_URL = "https://<project-ref>.supabase.co"
SUPABASE_KEY = "<anon-or-publishable-key>"
```

---

## Security notes
- No password or connection string is committed to git. Locally, secrets live in `.env` (git-ignored). In CI they come from GitHub Secrets; in deployment, from Streamlit Secrets.
- Row Level Security is enabled on every table, so Supabase's public API key cannot read or change them. The app connects with the database connection string instead.
