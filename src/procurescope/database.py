from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id UUID PRIMARY KEY,
    query_text TEXT NOT NULL,
    window_start DATE NOT NULL,
    window_end DATE NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    page_count INTEGER NOT NULL DEFAULT 0,
    received_count INTEGER NOT NULL DEFAULT 0,
    loaded_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS source_notice_versions (
    notice_key TEXT PRIMARY KEY,
    publication_number TEXT,
    notice_identifier TEXT,
    notice_version TEXT,
    publication_date DATE,
    title TEXT,
    buyer_name TEXT,
    buyer_country TEXT,
    deadline DATE,
    cpv_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    performance_locations JSONB NOT NULL DEFAULT '[]'::jsonb,
    procedure_identifier TEXT,
    form_type TEXT,
    notice_url TEXT,
    award_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_hash TEXT NOT NULL,
    source_payload JSONB NOT NULL,
    ingestion_run_id UUID REFERENCES ingestion_runs(run_id),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE source_notice_versions
    ADD COLUMN IF NOT EXISTS source_changed_at TIMESTAMPTZ;
UPDATE source_notice_versions
SET source_changed_at = first_seen_at
WHERE source_changed_at IS NULL;
ALTER TABLE source_notice_versions
    ALTER COLUMN source_changed_at SET DEFAULT now();
ALTER TABLE source_notice_versions
    ALTER COLUMN source_changed_at SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_notice_publication_date
    ON source_notice_versions (publication_date);
CREATE INDEX IF NOT EXISTS ix_notice_deadline
    ON source_notice_versions (deadline);
CREATE INDEX IF NOT EXISTS ix_notice_buyer_name
    ON source_notice_versions (buyer_name);
CREATE INDEX IF NOT EXISTS ix_notice_cpv_gin
    ON source_notice_versions USING GIN (cpv_codes);

CREATE TABLE IF NOT EXISTS rejected_records (
    rejection_id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES ingestion_runs(run_id),
    page_number INTEGER NOT NULL,
    reason TEXT NOT NULL,
    source_payload JSONB NOT NULL,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

UPSERT_NOTICE_SQL = """
INSERT INTO source_notice_versions (
    notice_key, publication_number, notice_identifier, notice_version,
    publication_date, title, buyer_name, buyer_country, deadline,
    cpv_codes, performance_locations, procedure_identifier, form_type,
    notice_url, award_fields, source_hash, source_payload,
    ingestion_run_id, first_seen_at, last_seen_at, source_changed_at, updated_at
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, now(), now(), now(), now()
)
ON CONFLICT (notice_key) DO UPDATE SET
    publication_number = EXCLUDED.publication_number,
    notice_identifier = EXCLUDED.notice_identifier,
    notice_version = EXCLUDED.notice_version,
    publication_date = EXCLUDED.publication_date,
    title = EXCLUDED.title,
    buyer_name = EXCLUDED.buyer_name,
    buyer_country = EXCLUDED.buyer_country,
    deadline = EXCLUDED.deadline,
    cpv_codes = EXCLUDED.cpv_codes,
    performance_locations = EXCLUDED.performance_locations,
    procedure_identifier = EXCLUDED.procedure_identifier,
    form_type = EXCLUDED.form_type,
    notice_url = EXCLUDED.notice_url,
    award_fields = EXCLUDED.award_fields,
    source_hash = EXCLUDED.source_hash,
    source_payload = EXCLUDED.source_payload,
    ingestion_run_id = EXCLUDED.ingestion_run_id,
    last_seen_at = now(),
    source_changed_at = CASE
        WHEN source_notice_versions.source_hash IS DISTINCT FROM EXCLUDED.source_hash
        THEN now()
        ELSE source_notice_versions.source_changed_at
    END,
    updated_at = now()
"""


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def ensure_schema(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(SCHEMA_SQL)

    def start_run(self, run_id: UUID, query: str, start: date, end: date) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                INSERT INTO ingestion_runs
                    (run_id, query_text, window_start, window_end, started_at, status)
                VALUES (%s, %s, %s, %s, %s, 'running')
                """,
                (run_id, query, start, end, datetime.now(UTC)),
            )

    def upsert_notices(self, notices: list[dict], run_id: UUID) -> None:
        if not notices:
            return
        values = [
            (
                notice["notice_key"],
                notice["publication_number"],
                notice["notice_identifier"],
                notice["notice_version"],
                notice["publication_date"],
                notice["title"],
                notice["buyer_name"],
                notice["buyer_country"],
                notice["deadline"],
                Jsonb(notice["cpv_codes"]),
                Jsonb(notice["performance_locations"]),
                notice["procedure_identifier"],
                notice["form_type"],
                notice["notice_url"],
                Jsonb(notice["award_fields"]),
                notice["source_hash"],
                Jsonb(json.loads(notice["source_payload"])),
                run_id,
            )
            for notice in notices
        ]
        with psycopg.connect(self.database_url) as connection:
            connection.executemany(UPSERT_NOTICE_SQL, values)

    def reject_records(
        self,
        run_id: UUID,
        page_number: int,
        records: list[tuple[str, dict]],
    ) -> None:
        if not records:
            return
        values = [
            (run_id, page_number, reason[:2000], Jsonb(record))
            for reason, record in records
        ]
        with psycopg.connect(self.database_url) as connection:
            connection.executemany(
                """
                INSERT INTO rejected_records (run_id, page_number, reason, source_payload)
                VALUES (%s, %s, %s, %s)
                """,
                values,
            )

    def finish_run(
        self,
        run_id: UUID,
        status: str,
        page_count: int,
        received_count: int,
        loaded_count: int,
        rejected_count: int,
        error_message: str | None = None,
    ) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                """
                UPDATE ingestion_runs
                SET finished_at = %s, status = %s, page_count = %s,
                    received_count = %s, loaded_count = %s, rejected_count = %s,
                    error_message = %s
                WHERE run_id = %s
                """,
                (
                    datetime.now(UTC),
                    status,
                    page_count,
                    received_count,
                    loaded_count,
                    rejected_count,
                    error_message,
                    run_id,
                ),
            )
