from __future__ import annotations

"""Minimal, dependency-free IP reputation clients.

Only the IP address and the user's own API key are sent to the selected
provider.  Results are normalized to :class:`IPReputation` dictionaries.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import __version__

ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
VIRUSTOTAL_IP_URL = "https://www.virustotal.com/api/v3/ip_addresses/{ip}"
USER_AGENT = f"NetworkMonitor/{__version__} (+https://github.com/AsemShahen/NetworkMonitor)"


def _error(ip: str, provider: str, key: str, *, message: str = "", args: dict | None = None) -> dict:
    return {
        "ip": ip,
        "provider": provider,
        "ok": False,
        "error_key": key,
        "error_args": dict(args or {}),
        "error": message,
        "checked": time.time(),
    }


def _request_json(request: urllib.request.Request, timeout: float) -> dict:
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload = response.read().decode("utf-8", errors="replace")
    data = json.loads(payload or "{}")
    return data if isinstance(data, dict) else {}


def _check_abuseipdb(ip: str, api_key: str, timeout: float) -> dict:
    query = urllib.parse.urlencode({"ipAddress": ip, "maxAgeInDays": "90", "verbose": ""})
    request = urllib.request.Request(
        f"{ABUSEIPDB_URL}?{query}",
        headers={
            "Accept": "application/json",
            "Key": api_key,
            "User-Agent": USER_AGENT,
        },
    )
    payload = _request_json(request, timeout)
    data = payload.get("data") or {}
    score = int(data.get("abuseConfidenceScore", 0) or 0)
    reports = int(data.get("totalReports", 0) or 0)
    return {
        "ip": ip,
        "provider": "abuseipdb",
        "ok": True,
        "score": max(0, min(100, score)),
        "reports": max(0, reports),
        "malicious": score >= 25 or reports >= 3,
        "country": str(data.get("countryCode") or ""),
        "isp": str(data.get("isp") or ""),
        "usage": str(data.get("usageType") or ""),
        "checked": time.time(),
        "raw": {
            "abuseConfidenceScore": score,
            "totalReports": reports,
            "lastReportedAt": data.get("lastReportedAt"),
            "isPublic": data.get("isPublic"),
            "domain": data.get("domain"),
        },
    }


def _check_virustotal(ip: str, api_key: str, timeout: float) -> dict:
    request = urllib.request.Request(
        VIRUSTOTAL_IP_URL.format(ip=urllib.parse.quote(ip, safe=":")),
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
    score = min(100, malicious_count * 10 + suspicious_count * 5)
    return {
        "ip": ip,
        "provider": "virustotal",
        "ok": True,
        "score": score,
        "reports": malicious_count + suspicious_count,
        "malicious": malicious_count > 0,
        "country": str(attributes.get("country") or ""),
        "isp": str(attributes.get("as_owner") or ""),
        "usage": str(attributes.get("network") or ""),
        "checked": time.time(),
        "raw": {
            "last_analysis_stats": stats,
            "total": total,
            "reputation": attributes.get("reputation"),
            "tags": attributes.get("tags") or [],
        },
    }


def check_ip(ip: str, provider: str = "abuseipdb", api_key: str = "", timeout: float = 8.0) -> dict:
    """Check one IP using the selected provider.

    The returned dictionary always has ``ok``; failures contain a translation
    key in ``error_key`` instead of leaking provider internals to the UI.
    """
    provider = (provider or "abuseipdb").strip().lower()
    ip = (ip or "").strip()
    if not ip:
        return _error(ip, provider, "security.error.no_ip")
    if not api_key:
        return _error(ip, provider, "security.error.no_api_key")
    try:
        if provider == "virustotal":
            return _check_virustotal(ip, api_key, timeout)
        return _check_abuseipdb(ip, api_key, timeout)
    except urllib.error.HTTPError as exc:
        message = ""
        try:
            message = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        return _error(
            ip,
            provider,
            "security.error.http",
            message=message,
            args={"code": exc.code},
        )
    except urllib.error.URLError as exc:
        return _error(
            ip,
            provider,
            "security.error.network",
            message=str(exc.reason or exc),
        )
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        return _error(ip, provider, "security.error.bad_response", message=str(exc))
    except Exception as exc:  # noqa: BLE001
        return _error(ip, provider, "security.error.network", message=str(exc))
