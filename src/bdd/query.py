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


CORRECT_PLAIN_QUESTION = text("""
WITH target AS (
  SELECT "id", "contenu"
  FROM "document"
  WHERE "id" = :doc_id
    AND "document_type" = 'exercise'
),
rebuilt AS (
  SELECT
    t."id",
    jsonb_agg(
      CASE
        WHEN e->>'type' = 'open' THEN
          e || jsonb_build_object(
                'questions',
                (
                  SELECT jsonb_agg(
                           CASE
                             WHEN q->>'id' = :id_question
                               THEN q
                                    || jsonb_build_object('is_corrected', true)
                                    || jsonb_build_object('is_correct', :is_correct)
                                    || jsonb_build_object('answers', :answer)
                             ELSE q
                           END
                         )
                  FROM jsonb_array_elements((e->'questions')::jsonb) AS q
                )
              )
        ELSE
          e
      END
    ) AS new_exercises
  FROM target t
  CROSS JOIN LATERAL jsonb_array_elements((t."contenu"::jsonb -> 'exercises')) AS e
  GROUP BY t."id"
)
UPDATE "document" d
SET "contenu" = ((d."contenu")::jsonb || jsonb_build_object('exercises', r.new_exercises))::json
FROM rebuilt r
WHERE d."id" = r."id";
                     
""")



MARK_IS_CORRECTED_QCM = text("""
WITH target AS (
  SELECT "id", "contenu"
  FROM "document"
  WHERE "id" = :doc_id
    AND "document_type" = 'exercise'
),
rebuilt AS (
  SELECT
    t."id",
    jsonb_agg(
      CASE
        WHEN e->>'type' = 'qcm' THEN
          e || jsonb_build_object(
                'questions',
                (
                  SELECT jsonb_agg(
                           CASE
                             WHEN q->>'id' = :id_question
                               THEN q || jsonb_build_object('is_corrected', true)
                             ELSE q
                           END
                         )
                  FROM jsonb_array_elements((e->'questions')::jsonb) AS q
                )
              )
        ELSE
          e
      END
    ) AS new_exercises
  FROM target t
  CROSS JOIN LATERAL jsonb_array_elements((t."contenu"::jsonb -> 'exercises')) AS e
  GROUP BY t."id"
)
UPDATE "document" d
SET "contenu" = ((d."contenu")::jsonb || jsonb_build_object('exercises', r.new_exercises))::json
FROM rebuilt r
WHERE d."id" = r."id";                  
""")

