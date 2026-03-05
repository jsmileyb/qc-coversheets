from app.services.review_form_service import ReviewFormService


def test_reviewer_identity_is_overridden_in_test_mode() -> None:
    service = ReviewFormService(test_mode=True)
    name, email = service._resolve_reviewer_identity("Live Reviewer", "live@example.com")
    assert name == "J Smiley Baltz"
    assert email == "jsbaltz@oulook.com"


def test_reviewer_identity_uses_database_values_when_not_test_mode() -> None:
    service = ReviewFormService(test_mode=False)
    name, email = service._resolve_reviewer_identity("Live Reviewer", "live@example.com")
    assert name == "Live Reviewer"
    assert email == "live@example.com"

