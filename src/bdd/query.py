from sqlalchemy import text

CLEAR_ALL_TABLES = text("""
DO $$
DECLARE
    tabname text;
BEGIN
    FOR tabname IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('TRUNCATE TABLE public.%I RESTART IDENTITY CASCADE;', tabname);
    END LOOP;
END $$;
""")


DROP_ALL_TABLES = text("""
DO $$
DECLARE
    tabname text;
BEGIN
    FOR tabname IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE;', tabname);
    END LOOP;
END $$;
""")

CHECK_TABLES = text("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
""")

FETCH_ALL_CHATS = text("""
SELECT s.id AS session_id,
    st.title,
    s.update_time
FROM sessions s
LEFT JOIN session_titles st ON s.id = st.session_id
WHERE s.user_id = :user_id AND st.is_deepcourse = FALSE
ORDER BY s.update_time DESC
""")

RENAME_SESSION = text("""
UPDATE session_titles
SET title = :title
WHERE session_id = :session_id
""")

CREATE_SESSION_TITLE = text("""
INSERT INTO session_titles (session_id, title, is_deepcourse)
VALUES (:session_id, :title, :is_deepcourse)
""")

STORE_BASIC_DOCUMENT = text("""
INSERT INTO public.document (id, google_sub, session_id, chapter_id, document_type, contenu, created_at, updated_at)
VALUES (:id, :google_sub, :session_id, :chapter_id, :document_type, :contenu, :created_at, :updated_at)
""")

RENAME_CHAT = text("""
UPDATE session_titles
SET title = :title
WHERE session_id = :session_id
""")

DELETE_CHAT = text("""
DELETE FROM sessions
WHERE id = :session_id
""")

RENAME_CHAPTER = text("""
UPDATE chapters
SET title = :title
WHERE id = :chapter_id
""")