
-- SELECT COUNT(*) AS chat_count
-- FROM "chat"
-- WHERE user_id = 'a4a06474-c8b5-4a81-b2fc-e89c1af2e671'

-- SELECT
--   to_timestamp(c.created_at)  AS created_at_dt,
--   to_timestamp(c.updated_at)  AS updated_at_dt,
--   u.name,
--   u.email,
--   c.id,
--   c.title,
--   c.meta::text AS tags,
--   c.chat::text AS chat
--   -- c.*
-- FROM chat AS c
-- JOIN "user" AS u
--   ON u.id = c.user_id
-- WHERE c.user_id = 'a4a06474-c8b5-4a81-b2fc-e89c1af2e671'
-- ORDER BY c.created_at DESC
-- LIMIT 5;

-- qc_coversheet_coversheet
-- discipline
-- review_request_discipline
-- project_execution_record

SELECT *
FROM qc_coversheet.project_execution_record
LIMIT 150

-- SELECT current_database();

-- SHOW search_path;

-- SELECT table_schema, table_name
-- FROM information_schema.tables
-- WHERE table_name = 'review_request'
-- ORDER BY table_schema;