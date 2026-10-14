from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timezone
from uuid import uuid4

from procurescope.config import Settings
from procurescope.database import Database
from procurescope.normalize import normalize_notice
from procurescope.storage import create_bronze_store
from procurescope.ted import TedSearchClient

LOGGER = logging.getLogger(__name__)
TED_FIELDS = [
    "publication-number",
    "notice-identifier",
    "notice-version",
    "publication-date",
    "notice-title",
    "title-proc",
    "buyer-name",
    "organisation-country-buyer",
    "deadline",
    "classification-cpv",
    "place-of-performance",
    "procedure-identifier",
    "form-type",
    "result-lot-identifier",
    "result-value-lot",
    "result-value-cur-lot",
    "result-value-notice",
    "result-value-cur-notice",
    "winner-name",
    "winner-identifier",
]


def run_pipeline(
    start_date: date,
    end_date: date,
    settings: Settings | None = None,
) -> dict:
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    settings = settings or Settings.from_env()
    run_id = uuid4()
    query = settings.query_for(start_date.isoformat(), end_date.isoformat())
    database = Database(settings.database_url)
    store = create_bronze_store(settings)
    client = TedSearchClient(settings.api_url, settings.page_size)
    database.ensure_schema()
    database.start_run(run_id, query, start_date, end_date)

    page_count = received_count = loaded_count = rejected_count = 0
    try:
        for page in client.iter_pages(query, TED_FIELDS):
            page_count += 1
            received = page.payload.get("notices", [])
            if not isinstance(received, list):
                raise ValueError(f"TED response page {page.page_number} has no notice list")
            received_count += len(received)
            checksum = hashlib.sha256(page.body).hexdigest()
            stamp = datetime.now(timezone.utc)
            raw_key = (
                f"ted/publication_date={stamp.date().isoformat()}/"
                f"run_id={run_id}/page_{page.page_number:04d}.json"
            )
            metadata = {
                "source": "TED Search API v3",
                "source_url": settings.api_url,
                "query": query,
                "window_start": start_date.isoformat(),
                "window_end": end_date.isoformat(),
                "run_id": str(run_id),
                "page_number": page.page_number,
                "fetched_at": stamp.isoformat(),
                "sha256": checksum,
                "notice_count": len(received),
                "iteration_continues": bool(page.iteration_next_token),
            }
            LOGGER.info(
                "Bronze page %s: %s notices (sha256=%s)",
                page.page_number,
                len(received),
                checksum[:12],
            )
            store.write_page(raw_key, page.body, metadata)

            normalized_page = []
            rejected_page = []
            for record in received:
                if not isinstance(record, dict):
                    rejected_page.append(
                        ("search result is not an object", {"value": record})
                    )
                    continue
                try:
                    normalized_page.append(normalize_notice(record))
                except (TypeError, ValueError, KeyError) as exc:
                    rejected_page.append((str(exc), record))

            database.upsert_notices(normalized_page, run_id)
            database.reject_records(run_id, page.page_number, rejected_page)
            loaded_count += len(normalized_page)
            rejected_count += len(rejected_page)

        database.finish_run(
            run_id,
            "succeeded",
            page_count,
            received_count,
            loaded_count,
            rejected_count,
        )
    except Exception as exc:
        database.finish_run(
            run_id,
            "failed",
            page_count,
            received_count,
            loaded_count,
            rejected_count,
            f"{type(exc).__name__}: {exc}",
        )
        raise

    report = {
        "run_id": str(run_id),
        "query": query,
        "pages": page_count,
        "received": received_count,
        "loaded": loaded_count,
        "rejected": rejected_count,
        "status": "succeeded",
    }
    LOGGER.info("Ingestion completed: %s", json.dumps(report, ensure_ascii=False))
    return report
