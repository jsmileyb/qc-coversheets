# Database Backup Scripts

This folder includes export and restore helpers for the QC Coversheet database.

## Prerequisites

- Python environment with dependencies installed (see project requirements).
- Database connection available via `DATABASE_URL` in `.env`, or pass `--database-url`.

## Export (backup)

Exports all tables from a schema to CSV files, plus a `manifest.json`.

```bash
python scripts/export_db_backup.py
```

Common options:

```bash
python scripts/export_db_backup.py --schema qc_coversheet --output backup --include-counts
python scripts/export_db_backup.py --database-url postgresql://user:pass@host:5432/dbname
```

Options:

- `--schema`: Schema to export. Defaults to `qc_coversheet`.
- `--output`: Root output directory for backups. A timestamped folder is created under this path.
- `--database-url`: Overrides `.env` `DATABASE_URL` for the connection.
- `--include-counts`: Adds per-table row counts to `manifest.json` (adds a `COUNT(*)` per table).

Output structure:

```
backup/
  20260309_120000_utc/
    qc_coversheet.app_permission.csv
    qc_coversheet.app_role.csv
    ...
    manifest.json
```

## Restore

Restores CSV backups into a schema. Uses `manifest.json` ordering when available.

```bash
python scripts/restore_db_backup.py backup/20260309_120000_utc
```

Common options:

```bash
python scripts/restore_db_backup.py backup/20260309_120000_utc --schema qc_coversheet --truncate
python scripts/restore_db_backup.py backup/20260309_120000_utc --database-url postgresql://user:pass@host:5432/dbname
```

Options:

- `backup_dir`: Required positional argument. Path to a backup folder created by the export script.
- `--schema`: Target schema to restore into. Defaults to `qc_coversheet`.
- `--database-url`: Overrides `.env` `DATABASE_URL` for the connection.
- `--truncate`: Truncates each table before loading and resets identity columns.

Notes:

- `--truncate` will clear each table before loading and reset identities.
- The restore script skips CSVs that do not match the target schema.
- If you change table names, rerun export so the backup filenames match.
