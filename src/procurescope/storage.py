from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class BronzeStore(Protocol):
    def write_page(self, key: str, body: bytes, metadata: dict) -> str: ...


class LocalBronzeStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write_page(self, key: str, body: bytes, metadata: dict) -> str:
        target = self.root.joinpath(*PurePosixPath(key).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        manifest_path = target.with_suffix(".manifest.json")
        manifest_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return str(target)


class S3BronzeStore:
    def __init__(
        self,
        endpoint_url: str | None,
        access_key: str | None,
        secret_key: str | None,
        bucket: str,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
            config=Config(
                connect_timeout=5,
                read_timeout=15,
                retries={"max_attempts": 8, "mode": "standard"},
            ),
        )
        try:
            self.client.head_bucket(Bucket=bucket)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            self.client.create_bucket(Bucket=bucket)

    def write_page(self, key: str, body: bytes, metadata: dict) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
            Metadata={"sha256": metadata["sha256"], "run-id": metadata["run_id"]},
        )
        manifest_key = str(PurePosixPath(key).with_suffix(".manifest.json"))
        self.client.put_object(
            Bucket=self.bucket,
            Key=manifest_key,
            Body=(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode(),
            ContentType="application/json",
        )
        return f"s3://{self.bucket}/{key}"


def create_bronze_store(settings) -> BronzeStore:
    if settings.storage_backend == "s3":
        return S3BronzeStore(
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket=settings.s3_bucket,
        )
    return LocalBronzeStore(settings.bronze_local_path)
