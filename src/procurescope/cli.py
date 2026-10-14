from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date, timedelta

from procurescope.config import Settings
from procurescope.database import Database
from procurescope.pipeline import run_pipeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="procurescope",
        description="Load TED public procurement notices into ProcureScope.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest = subparsers.add_parser("ingest", help="Fetch notices and load them to PostgreSQL.")
    ingest.add_argument("--from-date", type=date.fromisoformat, help="Inclusive ISO date.")
    ingest.add_argument("--to-date", type=date.fromisoformat, help="Inclusive ISO date.")
    ingest.add_argument(
        "--days",
        type=int,
        default=None,
        help="Load this many inclusive calendar days when --from-date is omitted.",
    )
    subparsers.add_parser("init-db", help="Create the database tables.")
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = _parser()
    args = parser.parse_args()
    settings = Settings.from_env()

    if args.command == "init-db":
        Database(settings.database_url).ensure_schema()
        print("ProcureScope schema is ready.")
        return

    if args.days is not None and args.days < 1:
        parser.error("--days must be a positive number")
    if args.from_date and args.days is not None:
        parser.error("--days cannot be combined with --from-date")

    today = date.today()
    if args.from_date:
        start_date = args.from_date
        end_date = args.to_date or today
    else:
        end_date = args.to_date or today
        days = args.days if args.days is not None else int(
            os.getenv("TED_DAYS_BACKFILL", "548")
        )
        if days < 1:
            parser.error("TED_DAYS_BACKFILL must be a positive number")
        start_date = end_date - timedelta(days=days - 1)

    if start_date > end_date:
        parser.error("--from-date must be on or before --to-date")

    report = run_pipeline(start_date, end_date, settings)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
