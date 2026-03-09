from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_admin_access
from app.auth.models import (
    AdminRoleItem,
    AdminUpdateUserRolesRequest,
    AdminUserAccessItem,
    AuthenticatedUser,
)
from app.auth.repository import AuthRepository
from app.db import get_pool
from app.state import get_auth_repository

router = APIRouter(prefix="/admin/user-access", tags=["user-access"])
ADMIN_INTERNAL_DOMAINS = {"greshamsmith.com", "gspnet.com"}
EXTERNAL_ALLOWED_ROLES = {"user", "reviewer"}


def is_internal_admin_email(email: str | None) -> bool:
    if not email or not email.strip():
        return False
    lowered = email.strip().lower()
    return any(lowered.endswith(f"@{domain}") for domain in ADMIN_INTERNAL_DOMAINS)


def has_external_only_roles(roles: list[str]) -> bool:
    return all(role in EXTERNAL_ALLOWED_ROLES for role in roles)


@router.get("/roles", response_model=list[AdminRoleItem], dependencies=[Depends(require_admin_access)])
async def list_roles(
    pool=Depends(get_pool),
    repo: AuthRepository = Depends(get_auth_repository),
) -> list[AdminRoleItem]:
    async with pool.acquire() as conn:
        rows = await repo.list_roles(conn)
    return [AdminRoleItem(**row) for row in rows]


@router.get("/users", response_model=list[AdminUserAccessItem], dependencies=[Depends(require_admin_access)])
async def list_users(
    pool=Depends(get_pool),
    repo: AuthRepository = Depends(get_auth_repository),
) -> list[AdminUserAccessItem]:
    async with pool.acquire() as conn:
        rows = await repo.list_app_users(conn)
    return [AdminUserAccessItem(**row) for row in rows]


@router.put("/users/{app_user_id}/roles", response_model=AdminUserAccessItem)
async def set_user_roles(
    app_user_id: UUID,
    payload: AdminUpdateUserRolesRequest,
    admin_user: AuthenticatedUser = Depends(require_admin_access),
    pool=Depends(get_pool),
    repo: AuthRepository = Depends(get_auth_repository),
) -> AdminUserAccessItem:
    if app_user_id == admin_user.app_user_id and "admin" not in payload.roles:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin role")

    try:
        async with pool.acquire() as conn:
            target_email = await repo.get_app_user_email(conn, app_user_id=app_user_id)
            if target_email is None:
                raise HTTPException(status_code=404, detail=f"User '{app_user_id}' not found")
            if not is_internal_admin_email(target_email):
                if not has_external_only_roles(payload.roles):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "External users can only be assigned the reviewer role."
                        ),
                    )
            await repo.set_user_roles(
                conn,
                app_user_id=app_user_id,
                role_names=payload.roles,
                is_active=payload.is_active,
                is_approved=payload.is_approved,
            )
            rows = await repo.list_app_users(conn)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    target = next((item for item in rows if item["app_user_id"] == app_user_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail=f"User '{app_user_id}' not found")
    return AdminUserAccessItem(**target)
