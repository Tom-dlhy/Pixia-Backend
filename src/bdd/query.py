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

DELETE_SESSION_TITLE = text("""
DELETE FROM session_titles
WHERE session_id = :session_id
""")

DELETE_DOCUMENTS = text("""
DELETE FROM document
WHERE session_id = :session_id
""")

RENAME_CHAPTER = text("""
UPDATE chapters
SET title = :title
WHERE id = :chapter_id
""")

DELETE_CHAPTER = text("""
DELETE FROM chapter
WHERE id = :chapter_id
""")

MARK_CHAPTER_COMPLETE = text("""
UPDATE chapter
SET is_complete = TRUE  
WHERE id = :chapter_id
""")

MARK_CHAPTER_UNCOMPLETE = text("""
UPDATE chapter
SET is_complete = FALSE
WHERE id = :chapter_id
""")

CHANGE_SETTINGS = text("""
UPDATE users
SET given_name = COALESCE(:new_given_name, given_name),
    family_name = COALESCE(:new_family_name, family_name),
    notion = COALESCE(:new_notion_url, notion),
    drive = COALESCE(:new_drive_url, drive)
WHERE google_sub = :user_id
""")

GET_SESSION_FROM_DOCUMENT = text("""
SELECT DISTINCT session_id 
FROM documents 
WHERE chapter_id = :chapter_id
""")

DELETE_DOCUMENTS_BY_CHAPTER = text("""
DELETE FROM document
WHERE chapter_id = :chapter_id
""")

LOGIN_USER = text("""
SELECT google_sub, given_name, family_name
FROM users
WHERE email = :email
""")

SIGNUP_USER = text("""
INSERT INTO users (google_sub, email, given_name, family_name)
VALUES (:google_sub, :email, :given_name, :family_name)
""")

CREATE_DEEPCOURSE= text(""" 
INSERT INTO public.deepcourses (id, title, google_sub, is_complete)
VALUES (:id, :title, :google_sub, :is_complete)
""")

CREATE_CHAPTER= text(""" 
INSERT INTO public.chapters (id, deepcourse_id, title)
VALUES (:id, :deepcourse_id, :title)
""")

UPDATE_DOCUMENT_CONTENT = text("""
UPDATE public.document
SET contenu = :contenu
WHERE session_id = :session_id
""")

