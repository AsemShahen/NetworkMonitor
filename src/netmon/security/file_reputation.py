from __future__ import annotations

"""On-demand SHA-256 hashing and malware reputation lookups."""

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import __version__

MALWAREBAZAAR_URL = "https://mb-api.abuse.ch/api/v1/"
VIRUSTOTAL_FILE_URL = "https://www.virustotal.com/api/v3/files/{sha256}"
USER_AGENT = f"NetworkMonitor/{__version__} (+https://github.com/AsemShahen/NetworkMonitor)"
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: str, should_stop=None) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            if should_stop is not None and should_stop():
                raise InterruptedError("hash interrupted")
            digest.update(chunk)
    return digest.hexdigest()


def _request_json(request: urllib.request.Request, timeout: float) -> dict:
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = response.read().decode("utf-8", errors="replace")
    data = json.loads(payload or "{}")
    return data if isinstance(data, dict) else {}


def _error(path: str, sha256: str, provider: str, key: str, *, message: str = "", args: dict | None = None) -> dict:
    return {
        "path": path,
        "sha256": sha256,
        "provider": provider,
        "ok": False,
        "error_key": key,
        "error_args": dict(args or {}),
        "error": message,
        "checked": time.time(),
    }


def _check_malwarebazaar(path: str, sha256: str, timeout: float) -> dict:
    body = urllib.parse.urlencode({"query": "get_info", "hash": sha256}).encode("utf-8")
    request = urllib.request.Request(
        MALWAREBAZAAR_URL,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    payload = _request_json(request, timeout)
    status = str(payload.get("query_status") or "").lower()
    if status in {"hash_not_found", "no_results", "illegal_hash", "invalid_hash"}:
        return {
            "path": path,
            "sha256": sha256,
            "provider": "malwarebazaar",
            "ok": True,
            "malicious": False,
            "detections": 0,
            "total": 0,
            "file_name": os.path.basename(path),
            "signatures": [],
            "tags": [],
            "checked": time.time(),
            "raw": {"query_status": status},
        }
    if status not in {"ok", ""}:
        return _error(
            path,
            sha256,
            "malwarebazaar",
            "security.error.provider",
            message=status,
            args={"status": status},
        )
    rows = payload.get("data") or []
    if not isinstance(rows, list) or not rows:
        return {
            "path": path,
            "sha256": sha256,
            "provider": "malwarebazaar",
            "ok": True,
            "malicious": False,
            "detections": 0,
            "total": 0,
            "file_name": os.path.basename(path),
            "signatures": [],
            "tags": [],
            "checked": time.time(),
            "raw": {"query_status": status},
        }
    first = rows[0] if isinstance(rows[0], dict) else {}
    signature = str(first.get("signature") or "")
    tags = first.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return {
        "path": path,
        "sha256": sha256,
        "provider": "malwarebazaar",
        "ok": True,
        "malicious": True,
        "detections": 1,
        "total": 1,
        "file_name": str(first.get("file_name") or os.path.basename(path)),
        "signatures": [signature] if signature else [],
        "tags": [str(tag) for tag in tags if tag],
        "checked": time.time(),
        "raw": {
            "query_status": status,
            "file_type": first.get("file_type"),
            "first_seen": first.get("first_seen"),
            "last_seen": first.get("last_seen"),
            "reporter": first.get("reporter"),
        },
    }


def _check_virustotal(path: str, sha256: str, api_key: str, timeout: float) -> dict:
    request = urllib.request.Request(
        VIRUSTOTAL_FILE_URL.format(sha256=sha256),
        headers={"Accept": "application/json", "x-apikey": api_key, "User-Agent": USER_AGENT},
    )
    payload = _request_json(request, timeout)
    attributes = ((payload.get("data") or {}).get("attributes") or {})
    stats = attributes.get("last_analysis_stats") or {}
    malicious_count = int(stats.get("malicious", 0) or 0)
    suspicious_count = int(stats.get("suspicious", 0) or 0)
    harmless = int(stats.get("harmless", 0) or 0)
    undetected = int(stats.get("undetected", 0) or 0)
    total = malicious_count + suspicious_count + harmless + undetected
    names = attributes.get("names") or []
    tags = attributes.get("tags") or []
    return {
        "path": path,
        "sha256": sha256,
        "provider": "virustotal",
        "ok": True,
        "malicious": malicious_count > 0,
        "detections": malicious_count,
        "total": total,
        "file_name": str(names[0]) if names else os.path.basename(path),
        "signatures": [],
        "tags": [str(tag) for tag in tags if tag],
        "checked": time.time(),
        "raw": {"last_analysis_stats": stats, "reputation": attributes.get("reputation")},
    }


def check_file_hash(
    path: str,
    sha256: str,
    provider: str = "malwarebazaar",
    api_key: str = "",
    timeout: float = 10.0,
) -> dict:
    provider = (provider or "malwarebazaar").strip().lower()
    if not sha256:
        return _error(path, sha256, provider, "security.error.no_hash")
    if provider == "virustotal" and not api_key:
        return _error(path, sha256, provider, "security.error.no_api_key")
    try:
        if provider == "virustotal":
            return _check_virustotal(path, sha256, api_key, timeout)
        return _check_malwarebazaar(path, sha256, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {
                "path": path,
                "sha256": sha256,
                "provider": provider,
                "ok": True,
                "malicious": False,
                "detections": 0,
                "total": 0,
                "file_name": os.path.basename(path),
                "signatures": [],
                "tags": [],
                "checked": time.time(),
                "raw": {"http_status": 404},
            }
        message = ""
        try:
            message = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        return _error(
            path,
            sha256,
            provider,
            "security.error.http",
            message=message,
            args={"code": exc.code},
        )
    except urllib.error.URLError as exc:
        return _error(
            path,
            sha256,
            provider,
            "security.error.network",
            message=str(exc.reason or exc),
        )
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        return _error(path, sha256, provider, "security.error.bad_response", message=str(exc))
    except Exception as exc:  # noqa: BLE001
        return _error(path, sha256, provider, "security.error.network", message=str(exc))
