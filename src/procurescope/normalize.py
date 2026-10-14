from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import quote


def _normal_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _lookup(record: dict[str, Any], *names: str) -> Any:
    wanted = {_normal_key(name) for name in names}
    for key, value in record.items():
        if _normal_key(str(key)) in wanted:
            return value
    return None


def _flatten_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str | int | float):
        result = str(value).strip()
        return result or None
    if isinstance(value, list):
        values = [_flatten_text(item) for item in value]
        return "; ".join(item for item in values if item) or None
    if isinstance(value, dict):
        for key in ("value", "text", "name", "label", "code", "id"):
            if key in value:
                result = _flatten_text(value[key])
                if result:
                    return result
        return None
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _parse_date(value: Any) -> date | None:
    text = _flatten_text(value)
    if not text:
        return None
    candidates = (text, text[:10], text.replace("-", "")[:8])
    for candidate in candidates:
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                pass
    return None


def _code_values(value: Any) -> list[str]:
    output: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            candidate = next(
                (item[key] for key in ("code", "value", "id") if key in item), None
            )
        else:
            candidate = item
        text = _flatten_text(candidate)
        if text:
            output.append(text)
    return list(dict.fromkeys(output))


def _places(value: Any) -> list[dict[str, Any]]:
    places: list[dict[str, Any]] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            place = {
                "country": _flatten_text(
                    _lookup(
                        item,
                        "place-of-performance-country-proc",
                        "place-of-performance-country-lot",
                        "country",
                        "country-code",
                    )
                ),
                "city": _flatten_text(
                    _lookup(
                        item,
                        "place-of-performance-city-proc",
                        "place-of-performance-city-lot",
                        "city",
                        "city-name",
                    )
                ),
                "nuts": _flatten_text(_lookup(item, "nuts", "country-subdivision")),
                "description": _flatten_text(
                    _lookup(item, "description", "region", "other")
                ),
            }
            places.append({key: val for key, val in place.items() if val})
        else:
            text = _flatten_text(item)
            if text:
                places.append({"code_or_text": text})
    return places


def normalize_notice(record: dict[str, Any]) -> dict[str, Any]:
    """Convert one TED search result to a stable, explicitly lossy Silver row."""
    publication_number = _flatten_text(
        _lookup(record, "publication-number", "ND")
    )
    notice_identifier = _flatten_text(
        _lookup(record, "notice-identifier", "notice-id")
    )
    publication_date = _parse_date(_lookup(record, "publication-date", "PD"))
    version = _flatten_text(_lookup(record, "notice-version", "version"))
    identity = notice_identifier or publication_number
    if not identity:
        raise ValueError("missing both publication-number and notice-identifier")

    # Publication number is retained as a separate source attribute. The key is
    # deterministic for a notice/version so repeated pulls are idempotent.
    version_identity = version or (publication_date.isoformat() if publication_date else "")
    notice_key = hashlib.sha256(
        f"{identity}|{version_identity}".encode("utf-8")
    ).hexdigest()

    title = _flatten_text(
        _lookup(
            record,
            "notice-title",
            "title-proc",
            "notice-title-proc",
            "title",
        )
    )
    buyer_name = _flatten_text(
        _lookup(
            record,
            "buyer-name",
            "organisation-name-buyer",
            "buyer",
        )
    )
    buyer_country = _flatten_text(
        _lookup(
            record,
            "buyer-country",
            "organisation-country-buyer",
        )
    )
    deadline = _parse_date(
        _lookup(record, "deadline", "deadline-date-lot", "deadline-date-part")
    )
    cpv_codes = _code_values(
        _lookup(record, "classification-cpv", "main-classification-proc")
    )
    locations = _places(
        _lookup(
            record,
            "place-of-performance",
            "place-of-performance-country-proc",
            "place-of-performance-country-lot",
        )
    )
    source_payload = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    source_hash = hashlib.sha256(source_payload.encode("utf-8")).hexdigest()

    award_fields = {
        name: _lookup(record, name)
        for name in (
            "result-lot-identifier",
            "result-value-lot",
            "result-value-cur-lot",
            "result-value-notice",
            "result-value-cur-notice",
            "winner-name",
            "winner-identifier",
        )
        if _lookup(record, name) is not None
    }
    notice_url = _flatten_text(_lookup(record, "notice-url", "url"))
    if not notice_url and publication_number:
        notice_url = (
            "https://ted.europa.eu/en/notice/-/detail/"
            f"{quote(publication_number, safe='-')}"
        )

    return {
        "notice_key": notice_key,
        "publication_number": publication_number,
        "notice_identifier": notice_identifier,
        "notice_version": version,
        "publication_date": publication_date,
        "title": title,
        "buyer_name": buyer_name,
        "buyer_country": buyer_country,
        "deadline": deadline,
        "cpv_codes": cpv_codes,
        "performance_locations": locations,
        "procedure_identifier": _flatten_text(
            _lookup(record, "procedure-identifier", "internal-identifier-proc")
        ),
        "form_type": _flatten_text(
            _lookup(record, "form-type", "notice-type", "notice-subtype")
        ),
        "notice_url": notice_url,
        "award_fields": award_fields,
        "source_hash": source_hash,
        "source_payload": source_payload,
    }
