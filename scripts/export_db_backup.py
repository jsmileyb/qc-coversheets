from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import asyncpg

from app.settings import get_settings


@dataclass
class TableExportResult:
    schema: str
    table: str
    file_name: str
    row_count: int | None
    error: str | None


def _quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export all tables from a schema into CSV backups.",
    )
    parser.add_argument(
        "--schema",
        default="qc_coversheet",
        help="Schema to export (default: qc_coversheet).",
    )
    parser.add_argument(
        "--output",
        default="backup",
        help="Directory to write backups (default: ./backup).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override database URL (default: read from .env).",
    )
    parser.add_argument(
        "--include-counts",
        action="store_true",
        help="Include per-table row counts in the manifest.",
    )
    return parser


async def _fetch_tables(conn: asyncpg.Connection, schema: str) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = $1
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """,
        schema,
    )
    return [row["table_name"] for row in rows]


async def _count_rows(conn: asyncpg.Connection, schema: str, table: str) -> int:
    query = f"SELECT COUNT(*) FROM {_quote_ident(schema)}.{_quote_ident(table)}"
    return await conn.fetchval(query)


async def _export_table(
    conn: asyncpg.Connection,
    schema: str,
    table: str,
    output_dir: Path,
    include_counts: bool,
) -> TableExportResult:
    file_name = f"{schema}.{table}.csv"
    output_path = output_dir / file_name

    row_count: int | None = None
    if include_counts:
        row_count = await _count_rows(conn, schema, table)

    query = f"SELECT * FROM {_quote_ident(schema)}.{_quote_ident(table)}"
    try:
        with output_path.open("wb") as handle:
            await conn.copy_from_query(query, output=handle, format="csv", header=True)
        return TableExportResult(schema, table, file_name, row_count, None)
    except Exception as exc:  # pragma: no cover - defensive logging in script
        return TableExportResult(schema, table, file_name, row_count, str(exc))


def _write_manifest(
    output_dir: Path, results: Iterable[TableExportResult], schema: str
) -> None:
    manifest = {
        "schema": schema,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tables": [asdict(item) for item in results],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


async def run_export(args: argparse.Namespace) -> int:
    settings = get_settings()
    database_url = args.database_url or settings.database_url
    schema = args.schema

    root_dir = Path(args.output).resolve()
    export_dir = root_dir / _timestamp_slug()
    export_dir.mkdir(parents=True, exist_ok=True)

    conn = await asyncpg.connect(dsn=database_url)
    try:
        tables = await _fetch_tables(conn, schema)
        if not tables:
            print(f"No tables found in schema '{schema}'.")
            return 1

        results = []
        for table in tables:
            result = await _export_table(
                conn, schema, table, export_dir, args.include_counts
            )
            results.append(result)
            if result.error:
                print(f"Failed: {schema}.{table}: {result.error}")
            else:
                print(f"Exported: {schema}.{table} -> {result.file_name}")

        _write_manifest(export_dir, results, schema)
        print(f"Backup written to {export_dir}")
        return 0
    finally:
        await conn.close()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(run_export(args))


if __name__ == "__main__":
    raise SystemExit(main())
