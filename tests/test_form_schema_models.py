import pytest
from pydantic import ValidationError

from app.models.forms import FormTemplateSchema


def _valid_schema() -> dict:
    return {
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


def test_form_template_schema_accepts_valid_contract() -> None:
    model = FormTemplateSchema.model_validate(_valid_schema())
    assert model.template_key == "qc_subconsultant_review"
    assert len(model.discipline_repeat.items) == 2


def test_form_template_schema_rejects_bad_choice_options() -> None:
    schema = _valid_schema()
    schema["discipline_repeat"]["items"][0]["choice"]["options"] = ["complete"]
    with pytest.raises(ValidationError):
        FormTemplateSchema.model_validate(schema)

