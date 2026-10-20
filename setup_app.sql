-- App setup: run this AFTER seed.sql.
-- Creates the tables the app writes to, an append-only audit log,
-- and a restricted "quiz_taker" role that quiz queries run as.

-- 1. Saved answers (written by the app when a signed-in user clicks Save)
CREATE TABLE IF NOT EXISTS saved_answers (
    id           BIGSERIAL PRIMARY KEY,
    user_id      UUID NOT NULL,
    user_email   TEXT NOT NULL,
    question_id  INT  NOT NULL,
    sql_text     TEXT NOT NULL,
    saved_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Audit log: one row every time someone runs or saves SQL
CREATE TABLE IF NOT EXISTS audit_log (
    id           BIGSERIAL PRIMARY KEY,
    user_email   TEXT NOT NULL,
    action       TEXT NOT NULL CHECK (action IN ('run', 'save')),
    question_id  INT,
    sql_text     TEXT,
    succeeded    BOOLEAN NOT NULL,
    logged_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Integrity check: the audit log is append-only.
--    UPDATE, DELETE and TRUNCATE are rejected for everyone, including the app.
CREATE OR REPLACE FUNCTION block_audit_changes() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only: % is not allowed', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS audit_log_no_update_delete ON audit_log;
CREATE TRIGGER audit_log_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION block_audit_changes();

DROP TRIGGER IF EXISTS audit_log_no_truncate ON audit_log;
CREATE TRIGGER audit_log_no_truncate
    BEFORE TRUNCATE ON audit_log
    FOR EACH STATEMENT EXECUTE FUNCTION block_audit_changes();

-- 4. Row Level Security on every table (blocks access through Supabase's public API keys)
ALTER TABLE universities  ENABLE ROW LEVEL SECURITY;
ALTER TABLE programs      ENABLE ROW LEVEL SECURITY;
ALTER TABLE admissions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log     ENABLE ROW LEVEL SECURITY;

-- 5. quiz_taker role: quiz queries run as this role.
--    It can only READ the 3 quiz tables. It has no access to saved_answers or audit_log.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'quiz_taker') THEN
        CREATE ROLE quiz_taker NOLOGIN;
    END IF;
END
$$;

GRANT quiz_taker TO postgres;   -- lets the app switch into this role
GRANT USAGE ON SCHEMA public TO quiz_taker;
GRANT SELECT ON universities, programs, admissions TO quiz_taker;
REVOKE ALL ON saved_answers, audit_log FROM quiz_taker;

-- RLS policies so quiz_taker can read the quiz tables
DROP POLICY IF EXISTS quiz_taker_read ON universities;
DROP POLICY IF EXISTS quiz_taker_read ON programs;
DROP POLICY IF EXISTS quiz_taker_read ON admissions;
CREATE POLICY quiz_taker_read ON universities FOR SELECT TO quiz_taker USING (true);
CREATE POLICY quiz_taker_read ON programs     FOR SELECT TO quiz_taker USING (true);
CREATE POLICY quiz_taker_read ON admissions   FOR SELECT TO quiz_taker USING (true);
