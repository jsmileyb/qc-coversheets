-- Migration: phase 2 seed data for form_template/form_template_version
-- Safe to re-run: uses ON CONFLICT and conditional inserts.

WITH upsert_template AS (
    INSERT INTO qc_coversheet.form_template (
        template_key, display_name, description, created_at, updated_at
    )
    VALUES (
        'qc_subconsultant_review',
        'QC Subconsultant Review Form',
        'Phase 2 default reviewer template',
        now(),
        now()
    )
    ON CONFLICT (template_key) DO UPDATE
    SET display_name = EXCLUDED.display_name,
        description = EXCLUDED.description,
        updated_at = now()
    RETURNING id
),
template_id AS (
    SELECT id FROM upsert_template
    UNION ALL
    SELECT id FROM qc_coversheet.form_template WHERE template_key = 'qc_subconsultant_review'
    LIMIT 1
)
INSERT INTO qc_coversheet.form_template_version (
    form_template_id, version, schema_json, is_active, created_at
)
SELECT
    t.id,
    1,
    '{
      "schema_version": "1.0",
      "template_key": "qc_subconsultant_review",
      "display_name": "QC Subconsultant Review Form",
      "branding": { "org_name": "Gresham Smith", "logo_url": "/static/images/logo.png" },
      "auto_fields": [
        "project_name",
        "project_number",
        "owner_end_user",
        "submittal_name",
        "submittal_date",
        "reviewer_name"
      ],
      "discipline_repeat": {
        "source": "review_request_discipline",
        "label_field": "discipline_name",
        "items": [
          {
            "section_key": "off_team_qualified_review",
            "section_label": "Off-Team Qualified Review",
            "choice": { "type": "single_select", "options": ["complete", "na"], "required": true },
            "signature": {
              "required_when_choice_selected": true,
              "type_name_must_match_reviewer": true,
              "match_mode": "case_insensitive_exact",
              "capture_timestamp": true
            },
            "notes": { "type": "text", "required": false, "max_length": 4000 }
          },
          {
            "section_key": "constructability_review",
            "section_label": "Constructability Review",
            "choice": { "type": "single_select", "options": ["complete", "na"], "required": true },
            "signature": {
              "required_when_choice_selected": true,
              "type_name_must_match_reviewer": true,
              "match_mode": "case_insensitive_exact",
              "capture_timestamp": true
            },
            "notes": { "type": "text", "required": false, "max_length": 4000 }
          }
        ]
      }
    }'::jsonb,
    true,
    now()
FROM template_id t
ON CONFLICT (form_template_id, version) DO UPDATE
SET schema_json = EXCLUDED.schema_json,
    is_active = true;

-- Ensure all other versions are inactive once v1 is seeded/updated.
UPDATE qc_coversheet.form_template_version ftv
SET is_active = false
FROM qc_coversheet.form_template ft
WHERE ftv.form_template_id = ft.id
  AND ft.template_key = 'qc_subconsultant_review'
  AND ftv.version <> 1;

-- Optional local seed for review_request and disciplines:
-- inserts only when enough source data exists.
DO $$
DECLARE
    v_template_id uuid;
    v_coversheet_id uuid;
    v_contact_id uuid;
    v_request_id uuid;
BEGIN
    SELECT id INTO v_template_id
    FROM qc_coversheet.form_template
    WHERE template_key = 'qc_subconsultant_review'
    LIMIT 1;

    SELECT id INTO v_coversheet_id
    FROM qc_coversheet.qc_coversheet_coversheet
    ORDER BY ingested_at DESC
    LIMIT 1;

    SELECT id INTO v_contact_id
    FROM qc_coversheet.contact
    ORDER BY updated_at DESC
    LIMIT 1;

    IF v_template_id IS NULL OR v_coversheet_id IS NULL OR v_contact_id IS NULL THEN
        RAISE NOTICE 'Skipping review_request seed (missing template/coversheet/contact).';
        RETURN;
    END IF;

    INSERT INTO qc_coversheet.review_request (
        qc_coversheet_coversheet_id,
        reviewer_contact_id,
        status,
        reviewer_name_used,
        expected_form_template_id,
        expected_form_version,
        created_at,
        updated_at
    )
    VALUES (
        v_coversheet_id,
        v_contact_id,
        'draft',
        'J Smiley Baltz',
        v_template_id,
        1,
        now(),
        now()
    )
    ON CONFLICT (qc_coversheet_coversheet_id, reviewer_contact_id) DO UPDATE
    SET expected_form_template_id = EXCLUDED.expected_form_template_id,
        expected_form_version = EXCLUDED.expected_form_version,
        reviewer_name_used = EXCLUDED.reviewer_name_used,
        updated_at = now()
    RETURNING id INTO v_request_id;

    IF v_request_id IS NULL THEN
        SELECT id INTO v_request_id
        FROM qc_coversheet.review_request
        WHERE qc_coversheet_coversheet_id = v_coversheet_id
          AND reviewer_contact_id = v_contact_id
        LIMIT 1;
    END IF;

    INSERT INTO qc_coversheet.review_request_discipline (review_request_id, discipline_id, created_at)
    SELECT v_request_id, d.id, now()
    FROM qc_coversheet.discipline d
    WHERE d.active = true
    ORDER BY d.updated_at DESC
    LIMIT 2
    ON CONFLICT (review_request_id, discipline_id) DO NOTHING;
END $$;
