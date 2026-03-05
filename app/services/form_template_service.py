from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import HTTPException

from app.models.forms import (
    FormTemplateRecord,
    FormTemplateSchema,
    FormTemplateVersionRecord,
    TemplateListItem,
    TemplateVersionListItem,
    TemplateVersionResponse,
)

if TYPE_CHECKING:
    import asyncpg


LIST_TEMPLATES_SQL = """
SELECT
    ft.template_key,
    ft.display_name,
    MAX(ftv.version) AS latest_version,
    MAX(ftv.version) FILTER (WHERE ftv.is_active) AS active_version
FROM qc_coversheet.form_template ft
LEFT JOIN qc_coversheet.form_template_version ftv
    ON ftv.form_template_id = ft.id
GROUP BY ft.id, ft.template_key, ft.display_name
ORDER BY ft.template_key;
"""

LIST_TEMPLATE_VERSIONS_SQL = """
SELECT
    ftv.version,
    ftv.is_active,
    ftv.created_at
FROM qc_coversheet.form_template ft
JOIN qc_coversheet.form_template_version ftv
    ON ftv.form_template_id = ft.id
WHERE ft.template_key = $1
ORDER BY ftv.created_at DESC, ftv.version DESC;
"""

GET_TEMPLATE_BY_KEY_SQL = """
SELECT id, template_key, display_name, description, created_at, updated_at
FROM qc_coversheet.form_template
WHERE template_key = $1;
"""

CREATE_TEMPLATE_SQL = """
INSERT INTO qc_coversheet.form_template (
    template_key, display_name, description, created_at, updated_at
)
VALUES ($1, $2, $3, now(), now())
RETURNING id, template_key, display_name, description, created_at, updated_at;
"""

GET_TEMPLATE_VERSION_SQL = """
SELECT
    ft.id AS template_id,
    ft.template_key,
    ft.display_name,
    ft.description,
    ft.created_at AS template_created_at,
    ft.updated_at AS template_updated_at,
    ftv.id AS version_id,
    ftv.form_template_id,
    ftv.version,
    ftv.schema_json,
    ftv.is_active,
    ftv.created_at AS version_created_at
FROM qc_coversheet.form_template ft
JOIN qc_coversheet.form_template_version ftv
    ON ftv.form_template_id = ft.id
WHERE ft.template_key = $1 AND ftv.version = $2;
"""

GET_MAX_VERSION_SQL = """
SELECT COALESCE(MAX(version), 0)
FROM qc_coversheet.form_template_version
WHERE form_template_id = $1;
"""

DEACTIVATE_VERSIONS_SQL = """
UPDATE qc_coversheet.form_template_version
SET is_active = false
WHERE form_template_id = $1 AND is_active = true;
"""

INSERT_TEMPLATE_VERSION_SQL = """
INSERT INTO qc_coversheet.form_template_version (
    form_template_id, version, schema_json, is_active, created_at
)
VALUES ($1, $2, $3::jsonb, true, now())
RETURNING id, form_template_id, version, schema_json, is_active, created_at;
"""

UPDATE_TEMPLATE_METADATA_SQL = """
UPDATE qc_coversheet.form_template
SET display_name = $2,
    description = COALESCE($3, description),
    updated_at = now()
WHERE id = $1
RETURNING id, template_key, display_name, description, created_at, updated_at;
"""


class FormTemplateService:
    @staticmethod
    def _ensure_schema_dict(value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="Stored form_template_version.schema_json is invalid JSON text",
                ) from exc
            if isinstance(parsed, dict):
                return parsed
        raise HTTPException(
            status_code=500,
            detail="Stored form_template_version.schema_json is not a JSON object",
        )

    async def list_templates(self, conn: asyncpg.Connection) -> list[TemplateListItem]:
        rows = await conn.fetch(LIST_TEMPLATES_SQL)
        return [
            TemplateListItem(
                template_key=row["template_key"],
                display_name=row["display_name"],
                latest_version=row["latest_version"],
                active_version=row["active_version"],
            )
            for row in rows
        ]

    async def list_template_versions(
        self, conn: asyncpg.Connection, template_key: str
    ) -> list[TemplateVersionListItem]:
        rows = await conn.fetch(LIST_TEMPLATE_VERSIONS_SQL, template_key)
        if not rows:
            template_exists = await conn.fetchrow(GET_TEMPLATE_BY_KEY_SQL, template_key)
            if template_exists is None:
                raise HTTPException(status_code=404, detail=f"Template '{template_key}' not found")
        return [
            TemplateVersionListItem(
                version=row["version"],
                is_active=row["is_active"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_template_version(
        self, conn: asyncpg.Connection, template_key: str, version: int
    ) -> TemplateVersionResponse:
        row = await conn.fetchrow(GET_TEMPLATE_VERSION_SQL, template_key, version)
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_key}' version '{version}' not found",
            )

        template = FormTemplateRecord(
            id=row["template_id"],
            template_key=row["template_key"],
            display_name=row["display_name"],
            description=row["description"],
            created_at=row["template_created_at"],
            updated_at=row["template_updated_at"],
        )
        version_record = FormTemplateVersionRecord(
            id=row["version_id"],
            form_template_id=row["form_template_id"],
            version=row["version"],
            schema_payload=self._ensure_schema_dict(row["schema_json"]),
            is_active=row["is_active"],
            created_at=row["version_created_at"],
        )
        return TemplateVersionResponse(template=template, version=version_record)

    async def create_new_version(
        self,
        conn: asyncpg.Connection,
        *,
        template_key: str,
        schema: FormTemplateSchema,
        description: str | None = None,
    ) -> TemplateVersionResponse:
        if schema.template_key != template_key:
            raise HTTPException(
                status_code=400,
                detail=f"Body template_key '{schema.template_key}' must match URL '{template_key}'",
            )

        async with conn.transaction():
            template_row = await conn.fetchrow(GET_TEMPLATE_BY_KEY_SQL, template_key)
            if template_row is None:
                template_row = await conn.fetchrow(
                    CREATE_TEMPLATE_SQL,
                    template_key,
                    schema.display_name,
                    description,
                )
            else:
                template_row = await conn.fetchrow(
                    UPDATE_TEMPLATE_METADATA_SQL,
                    template_row["id"],
                    schema.display_name,
                    description,
                )

            form_template_id = template_row["id"]
            max_version = await conn.fetchval(GET_MAX_VERSION_SQL, form_template_id)
            next_version = int(max_version) + 1

            await conn.execute(DEACTIVATE_VERSIONS_SQL, form_template_id)
            version_row = await conn.fetchrow(
                INSERT_TEMPLATE_VERSION_SQL,
                form_template_id,
                next_version,
                json.dumps(schema.model_dump()),
            )

        template = FormTemplateRecord(
            id=template_row["id"],
            template_key=template_row["template_key"],
            display_name=template_row["display_name"],
            description=template_row["description"],
            created_at=template_row["created_at"],
            updated_at=template_row["updated_at"],
        )
        version_record = FormTemplateVersionRecord(
            id=version_row["id"],
            form_template_id=version_row["form_template_id"],
            version=version_row["version"],
            schema_payload=self._ensure_schema_dict(version_row["schema_json"]),
            is_active=version_row["is_active"],
            created_at=version_row["created_at"],
        )
        return TemplateVersionResponse(template=template, version=version_record)
