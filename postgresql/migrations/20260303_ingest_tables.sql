-- Migration: ingest tracking and queue scaffolding
-- Date: 2026-03-03

CREATE TABLE IF NOT EXISTS qc_coversheet.ingest_event (
    event_id uuid PRIMARY KEY,
    qc_udic_id text NOT NULL,
    event_type text NOT NULL,
    event_time timestamptz NOT NULL,
    correlation_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('received', 'processing', 'processed', 'failed')),
    attempt_count integer NOT NULL DEFAULT 0,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ingest_event_status_last_seen
ON qc_coversheet.ingest_event (status, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS ix_ingest_event_qc_udic_id
ON qc_coversheet.ingest_event (qc_udic_id);

CREATE TABLE IF NOT EXISTS qc_coversheet.ingest_job (
    qc_udic_id text PRIMARY KEY,
    latest_event_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('queued', 'processing', 'done', 'failed')),
    attempt_count integer NOT NULL DEFAULT 0,
    run_after timestamptz,
    locked_at timestamptz,
    locked_by text,
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_ingest_job_latest_event
        FOREIGN KEY (latest_event_id)
        REFERENCES qc_coversheet.ingest_event(event_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS ix_ingest_job_status_run_after
ON qc_coversheet.ingest_job (status, run_after);
