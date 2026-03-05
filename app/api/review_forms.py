from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_pool
from app.models.forms import (
    ReviewFormContext,
    ReviewFormSubmissionRequest,
    ReviewFormSubmissionResponse,
    ReviewFormValidationResult,
)
from app.services.review_form_service import ReviewFormService
from app.state import get_review_form_service

router = APIRouter(tags=["review-forms"])


def _reviewer_guard() -> None:
    # TODO: wire to real auth/authorization in phase 3.
    return None


@router.get("/review-forms/{review_request_id}", response_model=ReviewFormContext, dependencies=[Depends(_reviewer_guard)])
async def get_review_form(
    review_request_id: UUID,
    pool=Depends(get_pool),
    service: ReviewFormService = Depends(get_review_form_service),
) -> ReviewFormContext:
    async with pool.acquire() as conn:
        return await service.resolve_review_form(conn, review_request_id)


@router.post(
    "/review-forms/{review_request_id}/validate",
    response_model=ReviewFormValidationResult,
    dependencies=[Depends(_reviewer_guard)],
)
async def validate_review_form(
    review_request_id: UUID,
    payload: ReviewFormSubmissionRequest,
    pool=Depends(get_pool),
    service: ReviewFormService = Depends(get_review_form_service),
) -> ReviewFormValidationResult:
    async with pool.acquire() as conn:
        context = await service.resolve_review_form(conn, review_request_id)
    if payload.review_request_id and payload.review_request_id != review_request_id:
        raise HTTPException(
            status_code=400,
            detail="Payload review_request_id does not match URL review_request_id",
        )
    return service.validate_submission_payload(context=context, submission=payload)


@router.post(
    "/review-forms/{review_request_id}/submit",
    response_model=ReviewFormSubmissionResponse,
    dependencies=[Depends(_reviewer_guard)],
)
async def submit_review_form(
    review_request_id: UUID,
    payload: ReviewFormSubmissionRequest,
    pool=Depends(get_pool),
    service: ReviewFormService = Depends(get_review_form_service),
) -> ReviewFormSubmissionResponse:
    async with pool.acquire() as conn:
        context = await service.resolve_review_form(conn, review_request_id)
        if payload.review_request_id and payload.review_request_id != review_request_id:
            raise HTTPException(
                status_code=400,
                detail="Payload review_request_id does not match URL review_request_id",
            )
        validation = service.validate_submission_payload(context=context, submission=payload)
        if not validation.valid:
            raise HTTPException(status_code=422, detail=validation.errors)
        return await service.submit_review_form(conn, context=context, submission=payload)

