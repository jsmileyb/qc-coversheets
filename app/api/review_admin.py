from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.db import get_pool
from app.models.forms import (
    ActiveReviewRequestItem,
    ReassignTemplateVersionRequest,
    ReassignTemplateVersionResponse,
)
from app.services.review_admin_service import ReviewAdminService
from app.state import get_review_admin_service

router = APIRouter(prefix="/admin/review-requests", tags=["review-admin"])


def _admin_guard() -> None:
    # TODO: wire to real auth/authorization in phase 3.
    return None


@router.get("/active", response_model=list[ActiveReviewRequestItem], dependencies=[Depends(_admin_guard)])
async def list_active_review_requests(
    pool=Depends(get_pool),
    service: ReviewAdminService = Depends(get_review_admin_service),
) -> list[ActiveReviewRequestItem]:
    async with pool.acquire() as conn:
        return await service.list_active_review_requests(conn)


@router.post(
    "/{review_request_id}/reassign-template",
    response_model=ReassignTemplateVersionResponse,
    dependencies=[Depends(_admin_guard)],
)
async def reassign_template_version(
    review_request_id: UUID,
    payload: ReassignTemplateVersionRequest,
    pool=Depends(get_pool),
    service: ReviewAdminService = Depends(get_review_admin_service),
) -> ReassignTemplateVersionResponse:
    async with pool.acquire() as conn:
        return await service.reassign_review_request_template(
            conn,
            review_request_id=review_request_id,
            template_key=payload.template_key,
            version=payload.version,
        )

