from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_url: str
    page_size: int
    query_template: str
    database_url: str
    storage_backend: str
    bronze_local_path: Path
    s3_endpoint_url: str | None
    s3_access_key: str | None
    s3_secret_key: str | None
    s3_bucket: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            api_url=os.getenv(
                "TED_API_URL", "https://api.ted.europa.eu/v3/notices/search"
            ),
            page_size=int(os.getenv("TED_PAGE_SIZE", "100")),
            query_template=os.getenv(
                "TED_QUERY_TEMPLATE",
                "publication-date = ({start} <> {end}) AND "
                "classification-cpv = 72* AND place-of-performance IN (POL)",
            ),
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql://procurescope:procurescope@localhost:5432/procurescope",
            ),
            storage_backend=os.getenv("STORAGE_BACKEND", "local").lower(),
            bronze_local_path=Path(os.getenv("BRONZE_LOCAL_PATH", "data/bronze")),
            s3_endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            s3_access_key=os.getenv("S3_ACCESS_KEY"),
            s3_secret_key=os.getenv("S3_SECRET_KEY"),
            s3_bucket=os.getenv("S3_BUCKET", "procurescope-bronze"),
        )

    def query_for(self, start_date: str, end_date: str) -> str:
        """Build an Expert Search query from ISO dates."""
        start = start_date.replace("-", "")
        end = end_date.replace("-", "")
        return self.query_template.format(start=start, end=end)
