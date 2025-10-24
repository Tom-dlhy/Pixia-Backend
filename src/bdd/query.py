from sqlalchemy import text

CLEAR_ALL_TABLES = text(
    """
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
"""
)


DROP_ALL_TABLES = text(
    """
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
"""
)

CHECK_TABLES = text(
    """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"""
)

FETCH_ALL_CHATS = text(
    """
SELECT 
    session_id AS session_id,
    document_type AS document_type,
    COALESCE(
        (contenu::jsonb->>'title'),
        CASE
            WHEN document_type = 'exercise' THEN 'Exercice'
            WHEN document_type = 'course' THEN 'Cours'
            ELSE 'Document'
        END
    ) AS title
FROM document
WHERE google_sub = :user_id
  AND chapter_id IS NULL
  AND google_sub IS NOT NULL
ORDER BY updated_at DESC
"""
)


STORE_BASIC_DOCUMENT = text(
    """
INSERT INTO public.document (id, google_sub, session_id, chapter_id, document_type, contenu, created_at, updated_at)
VALUES (:id, :google_sub, :session_id, :chapter_id, :document_type, :contenu, :created_at, :updated_at)
"""
)


DELETE_DOCUMENTS = text(
    """
DELETE FROM document
WHERE session_id = :session_id
"""
)

DELETE_DEEPCOURSE = text(
    """
BEGIN;

-- Récupérer les IDs des sessions associées aux documents des chapitres
WITH sessions_to_delete AS (
    SELECT DISTINCT "session_id"
    FROM "public"."document"
    WHERE "chapter_id" IN (
        SELECT "id"
        FROM "public"."chapter"
        WHERE "deep_course_id" = :deepcourse_id
    )
)
-- Supprimer les sessions
DELETE FROM "public"."sessions"
WHERE "id" IN (SELECT "session_id" FROM sessions_to_delete);

-- Supprimer tous les documents associés aux chapitres du deepcourse
DELETE FROM "public"."document"
WHERE "chapter_id" IN (
    SELECT "id"
    FROM "public"."chapter"
    WHERE "deep_course_id" = :deepcourse_id
);

-- Supprimer tous les chapitres du deepcourse
DELETE FROM "public"."chapter"
WHERE "deep_course_id" = :deepcourse_id;

-- Supprimer le deepcourse lui-même
DELETE FROM "public"."deepcourse"
WHERE "id" = :deepcourse_id
  AND "google_sub" = :user_id;

COMMIT;
"""
)

RENAME_CHAPTER = text(
    """
UPDATE chapters
SET title = :title
WHERE id = :chapter_id
"""
)

DELETE_CHAPTER = text(
    """
DELETE FROM chapter
WHERE id = :chapter_id
"""
)

MARK_CHAPTER_COMPLETE = text(
    """
UPDATE chapter
SET is_complete = TRUE  
WHERE id = :chapter_id
"""
)

MARK_CHAPTER_UNCOMPLETE = text(
    """
UPDATE chapter
SET is_complete = FALSE
WHERE id = :chapter_id
"""
)

FETCH_CHAPTER_DOCUMENTS = text(
    """
SELECT 
    MAX(CASE WHEN "document_type" = 'exercise' THEN "session_id" END) AS exercice_session_id,
    MAX(CASE WHEN "document_type" = 'course' THEN "session_id" END) AS course_session_id,
    MAX(CASE WHEN "document_type" = 'eval' THEN "session_id" END) AS evaluation_session_id
FROM "public"."document"
WHERE "chapter_id" = :chapter_id
GROUP BY "chapter_id"
"""
)

CHANGE_SETTINGS = text(
    """
UPDATE users
SET name = COALESCE(:new_given_name, name),
    notion_token = COALESCE(:new_notion_token, notion_token),
    study = COALESCE(:new_niveau_etude, study)
WHERE google_sub = :user_id
"""
)

GET_SESSION_FROM_DOCUMENT = text(
    """
SELECT DISTINCT session_id 
FROM documents 
WHERE chapter_id = :chapter_id
"""
)

DELETE_DOCUMENTS_BY_CHAPTER = text(
    """
DELETE FROM document
WHERE chapter_id = :chapter_id
"""
)

LOGIN_USER = text(
    """
SELECT google_sub, email, name, notion_token, study
FROM users
WHERE email = :email
"""
)

SIGNUP_USER = text(
    """
INSERT INTO users (google_sub, email, created_at, name, notion_token, study)
VALUES (:google_sub, :email, :created_at, :name, :notion_token, :study)
RETURNING google_sub, email, name, notion_token, study
"""
)


CORRECT_PLAIN_QUESTION = text(
    """
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
                     
"""
)


MARK_IS_CORRECTED_QCM = text(
    """
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
"""
)


CREATE_DEEPCOURSE = text(
    """ 
INSERT INTO public.deepcourse (id, titre, google_sub)
VALUES (:id, :titre, :google_sub)
"""
)

CREATE_CHAPTER = text(
    """ 
INSERT INTO public.chapter (id, deep_course_id, titre, is_complete)
VALUES (:id, :deep_course_id, :titre, :is_complete)
"""
)

FETCH_ALL_CHAPTERS = text(
    """
SELECT id as chapter_id, titre as title, is_complete
FROM public.chapter
WHERE deep_course_id = :deep_course_id
"""
)

UPDATE_DOCUMENT_CONTENT = text(
    """
UPDATE public.document
SET contenu = :contenu
WHERE session_id = :session_id
"""
)

FETCH_DOCUMENT_BY_SESSION = text(
    """
SELECT *
FROM public.document
WHERE session_id = :session_id
"""
)

GET_DEEPCOURSE_AND_CHAPTER_FROM_ID = text(
    """
SELECT c.titre as chapter_title, d.titre as deepcourse_title
FROM chapter c 
LEFT JOIN deepcourse d 
ON c.deep_course_id = d.id
WHERE d.id = :deepcourse_id
       """
)
FETCH_ALL_DEEPCOURSES = text(
    """
SELECT 
    "d"."id" AS deepcourse_id, 
    "d"."titre" AS title,
    ROUND(
        CAST(SUM(CASE WHEN "c"."is_complete" THEN 1 ELSE 0 END) AS NUMERIC) / 
        NULLIF(COUNT("c"."id"), 0), 
        2
    ) AS completion
FROM "public"."deepcourse" AS "d"
JOIN "public"."chapter" AS "c" ON "d"."id" = "c"."deep_course_id"
WHERE "d"."google_sub" = :user_id
GROUP BY "d"."id", "d"."titre"
ORDER BY "d"."id";
"""
)
