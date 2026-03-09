from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Iterable

import asyncpg

from app.settings import get_settings


def _quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restore CSV backups into a database schema.",
    )
    parser.add_argument(
        "backup_dir",
        help="Path to a backup directory created by export_db_backup.py.",
    )
    parser.add_argument(
        "--schema",
        default="qc_coversheet",
        help="Schema to restore into (default: qc_coversheet).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override database URL (default: read from .env).",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate tables before restore.",
    )
    return parser


def _load_manifest(backup_dir: Path) -> list[str] | None:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        return None

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    tables = []
    for item in payload.get("tables", []):
        table = item.get("table")
        schema = item.get("schema")
        if table and schema:
            tables.append(f"{schema}.{table}.csv")
    return tables


def _discover_csv_files(backup_dir: Path) -> list[Path]:
    csv_files = sorted(backup_dir.glob("*.csv"))
    return [path for path in csv_files if path.is_file()]


def _iter_restore_files(backup_dir: Path) -> Iterable[Path]:
    manifest_files = _load_manifest(backup_dir)
    if manifest_files:
        for entry in manifest_files:
            path = backup_dir / entry
            if path.exists():
                yield path
        return

    for path in _discover_csv_files(backup_dir):
        yield path


def _split_name(file_name: str) -> tuple[str, str] | None:
    if not file_name.endswith(".csv"):
        return None
    stem = file_name[:-4]
    parts = stem.split(".")
    if len(parts) < 2:
        return None
    schema = parts[0]
    table = ".".join(parts[1:])
    return schema, table


async def _truncate_table(conn: asyncpg.Connection, schema: str, table: str) -> None:
    query = f"TRUNCATE TABLE {_quote_ident(schema)}.{_quote_ident(table)} RESTART IDENTITY CASCADE"
    await conn.execute(query)


async def _restore_table(
    conn: asyncpg.Connection,
    schema: str,
    table: str,
    csv_path: Path,
) -> None:
    query = (
        f"COPY {_quote_ident(schema)}.{_quote_ident(table)} FROM STDIN WITH CSV HEADER"
    )
    with csv_path.open("rb") as handle:
        await conn.copy_to_table(query=query, source=handle)


async def run_restore(args: argparse.Namespace) -> int:
    settings = get_settings()
    database_url = args.database_url or settings.database_url
    backup_dir = Path(args.backup_dir).resolve()
    schema = args.schema

    if not backup_dir.exists():
        print(f"Backup directory not found: {backup_dir}")
        return 1

    conn = await asyncpg.connect(dsn=database_url)
    try:
        for csv_path in _iter_restore_files(backup_dir):
            name_parts = _split_name(csv_path.name)
            if not name_parts:
                print(f"Skipping file with unexpected name: {csv_path.name}")
                continue

            file_schema, table = name_parts
            if file_schema != schema:
                print(
                    f"Skipping {csv_path.name}: schema mismatch ({file_schema} != {schema})"
                )
                continue

            if args.truncate:
                await _truncate_table(conn, schema, table)
            await _restore_table(conn, schema, table, csv_path)
            print(f"Restored: {schema}.{table} <- {csv_path.name}")

        return 0
    finally:
        await conn.close()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(run_restore(args))


if __name__ == "__main__":
    raise SystemExit(main())
