from datetime import datetime, timezone
from uuid import uuid4

from app.models.forms import (
    DisciplineAnswer,
    DisciplineResolved,
    FormTemplateSchema,
    ReviewFormContext,
    ReviewFormSubmissionRequest,
    SectionAnswer,
)
from app.services.review_form_service import ReviewFormService


def _schema() -> FormTemplateSchema:
    return FormTemplateSchema.model_validate(
        {
            "schema_version": "1.0",
            "template_key": "qc_subconsultant_review",
            "display_name": "QC Subconsultant Review Form",
            "branding": {"org_name": "Gresham Smith", "logo_url": None},
            "auto_fields": [
                "project_name",
                "project_number",
                "owner_end_user",
                "submittal_name",
                "submittal_date",
                "reviewer_name",
            ],
            "discipline_repeat": {
                "source": "review_request_discipline",
                "label_field": "discipline_name",
                "items": [
                    {
                        "section_key": "off_team_qualified_review",
                        "section_label": "Off-Team Qualified Review",
                        "choice": {"type": "single_select", "options": ["complete", "na"], "required": True},
                        "signature": {
                            "required_when_choice_selected": True,
                            "type_name_must_match_reviewer": True,
                            "match_mode": "case_insensitive_exact",
                            "capture_timestamp": True,
                        },
                        "notes": {"type": "text", "required": False, "max_length": 4000},
                    },
                    {
                        "section_key": "constructability_review",
                        "section_label": "Constructability Review",
                        "choice": {"type": "single_select", "options": ["complete", "na"], "required": True},
                        "signature": {
                            "required_when_choice_selected": True,
                            "type_name_must_match_reviewer": True,
                            "match_mode": "case_insensitive_exact",
                            "capture_timestamp": True,
                        },
                        "notes": {"type": "text", "required": False, "max_length": 4000},
                    },
                ],
            },
        }
    )


def _context() -> tuple[ReviewFormContext, str]:
    discipline_id = str(uuid4())
    context = ReviewFormContext(
        review_request_id=uuid4(),
        form_template_id=uuid4(),
        form_version=1,
        template_key="qc_subconsultant_review",
        reviewer_name="Jane Reviewer",
        reviewer_email="jane@example.com",
        auto_values={"project_name": "Project"},
        disciplines=[DisciplineResolved(discipline_id=discipline_id, discipline_name="Structural")],
        schema_json=_schema(),
    )
    return context, discipline_id


def test_validate_submission_accepts_case_insensitive_signature_match() -> None:
    service = ReviewFormService()
    context, discipline_id = _context()
    now = datetime.now(timezone.utc)
    payload = ReviewFormSubmissionRequest(
        review_request_id=context.review_request_id,
        reviewer_name_expected=context.reviewer_name,
        discipline_responses=[
            DisciplineAnswer(
                discipline_id=discipline_id,
                discipline_name="Structural",
                sections={
                    "off_team_qualified_review": SectionAnswer(
                        status="complete",
                        signature_name="  jane reviewer  ",
                        signed_at=now,
                        notes="",
                    ),
                    "constructability_review": SectionAnswer(
                        status="na",
                        signature_name="JANE REVIEWER",
                        signed_at=now,
                        notes="",
                    ),
                },
            )
        ],
    )

    result = service.validate_submission_payload(context=context, submission=payload)
    assert result.valid
    assert result.errors == []


def test_validate_submission_rejects_missing_section() -> None:
    service = ReviewFormService()
    context, discipline_id = _context()
    now = datetime.now(timezone.utc)
    payload = ReviewFormSubmissionRequest(
        discipline_responses=[
            DisciplineAnswer(
                discipline_id=discipline_id,
                discipline_name="Structural",
                sections={
                    "off_team_qualified_review": SectionAnswer(
                        status="complete",
                        signature_name="Jane Reviewer",
                        signed_at=now,
                        notes="",
                    )
                },
            )
        ],
    )

    result = service.validate_submission_payload(context=context, submission=payload)
    assert not result.valid
    assert any("missing sections" in err for err in result.errors)

