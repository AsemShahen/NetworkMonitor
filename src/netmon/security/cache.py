from __future__ import annotations

"""SQLite cache for IP and file reputation results.

The cache lives in its own database so reputation writes never compete with
the single-writer usage database.  It uses WAL mode for concurrent reads from
the GUI and the reputation worker threads.
"""

import json
import sqlite3
import threading
import time
from pathlib import Path

from ..config import DATA_DIR

SECURITY_DB = DATA_DIR / "security.db"
IP_CACHE_SECONDS = 24 * 60 * 60
FILE_CACHE_SECONDS = 7 * 24 * 60 * 60


class SecurityStore:
    def __init__(self, path: Path = SECURITY_DB):
        self.path = Path(path)
        self._lock = threading.RLock()
        self.last_error: str | None = None
        self._conn: sqlite3.Connection | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(
                str(self.path),
                timeout=5.0,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            with self._lock:
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA busy_timeout=5000")
                self._conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS ip_reputation (
                        ip TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        checked REAL NOT NULL,
                        score INTEGER NOT NULL DEFAULT 0,
                        reports INTEGER NOT NULL DEFAULT 0,
                        malicious INTEGER NOT NULL DEFAULT 0,
                        country TEXT NOT NULL DEFAULT '',
                        isp TEXT NOT NULL DEFAULT '',
                        usage TEXT NOT NULL DEFAULT '',
                        raw TEXT NOT NULL DEFAULT '',
                        PRIMARY KEY (ip, provider)
                    );
                    CREATE TABLE IF NOT EXISTS file_reputation (
                        sha256 TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        checked REAL NOT NULL,
                        malicious INTEGER NOT NULL DEFAULT 0,
                        detections INTEGER NOT NULL DEFAULT 0,
                        total INTEGER NOT NULL DEFAULT 0,
                        file_name TEXT NOT NULL DEFAULT '',
                        signatures TEXT NOT NULL DEFAULT '',
                        tags TEXT NOT NULL DEFAULT '',
                        raw TEXT NOT NULL DEFAULT '',
                        PRIMARY KEY (sha256, provider)
                    );
                    CREATE TABLE IF NOT EXISTS blocked_ips (
                        ip TEXT PRIMARY KEY,
                        blocked_at REAL NOT NULL,
                        reason TEXT NOT NULL DEFAULT ''
                    );
                    """
                )
                self._conn.commit()
        except (OSError, sqlite3.Error) as exc:
            self.last_error = str(exc)
            if self._conn is not None:
                try:
                    self._conn.close()
                except sqlite3.Error:
                    pass
                self._conn = None

    # ------------------------------------------------------------------ IP cache
    def get_ip(self, ip: str, provider: str, max_age: float = IP_CACHE_SECONDS) -> dict | None:
        if self._conn is None or not ip:
            return None
        try:
            with self._lock:
                row = self._conn.execute(
                    "SELECT * FROM ip_reputation WHERE ip = ? AND provider = ?",
                    (ip, provider),
                ).fetchone()
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return None
        if row is None or time.time() - float(row["checked"] or 0.0) > max_age:
            return None
        return {
            "ip": row["ip"],
            "provider": row["provider"],
            "ok": True,
            "score": int(row["score"] or 0),
            "reports": int(row["reports"] or 0),
            "malicious": bool(row["malicious"]),
            "country": row["country"] or "",
            "isp": row["isp"] or "",
            "usage": row["usage"] or "",
            "checked": float(row["checked"] or 0.0),
            "cached": True,
        }

    def put_ip(self, result: dict) -> None:
        if self._conn is None or not result.get("ip"):
            return
        try:
            with self._lock, self._conn:
                self._conn.execute(
                    """
                    INSERT INTO ip_reputation
                        (ip, provider, checked, score, reports, malicious,
                         country, isp, usage, raw)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ip, provider) DO UPDATE SET
                        checked = excluded.checked,
                        score = excluded.score,
                        reports = excluded.reports,
                        malicious = excluded.malicious,
                        country = excluded.country,
                        isp = excluded.isp,
                        usage = excluded.usage,
                        raw = excluded.raw
                    """,
                    (
                        str(result.get("ip") or ""),
                        str(result.get("provider") or ""),
                        float(result.get("checked") or time.time()),
                        int(result.get("score") or 0),
                        int(result.get("reports") or 0),
                        1 if result.get("malicious") else 0,
                        str(result.get("country") or ""),
                        str(result.get("isp") or ""),
                        str(result.get("usage") or ""),
                        json.dumps(result.get("raw") or {}, ensure_ascii=False),
                    ),
                )
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    # ---------------------------------------------------------------- file cache
    def get_file(self, sha256: str, provider: str, max_age: float = FILE_CACHE_SECONDS) -> dict | None:
        if self._conn is None or not sha256:
            return None
        try:
            with self._lock:
                row = self._conn.execute(
                    "SELECT * FROM file_reputation WHERE sha256 = ? AND provider = ?",
                    (sha256, provider),
                ).fetchone()
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return None
        if row is None or time.time() - float(row["checked"] or 0.0) > max_age:
            return None
        return {
            "sha256": row["sha256"],
            "provider": row["provider"],
            "ok": True,
            "malicious": bool(row["malicious"]),
            "detections": int(row["detections"] or 0),
            "total": int(row["total"] or 0),
            "file_name": row["file_name"] or "",
            "signatures": self._load_list(row["signatures"]),
            "tags": self._load_list(row["tags"]),
            "checked": float(row["checked"] or 0.0),
            "cached": True,
        }

    def put_file(self, result: dict) -> None:
        if self._conn is None or not result.get("sha256"):
            return
        try:
            with self._lock, self._conn:
                self._conn.execute(
                    """
                    INSERT INTO file_reputation
                        (sha256, provider, checked, malicious, detections,
                         total, file_name, signatures, tags, raw)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sha256, provider) DO UPDATE SET
                        checked = excluded.checked,
                        malicious = excluded.malicious,
                        detections = excluded.detections,
                        total = excluded.total,
                        file_name = excluded.file_name,
                        signatures = excluded.signatures,
                        tags = excluded.tags,
                        raw = excluded.raw
                    """,
                    (
                        str(result.get("sha256") or ""),
                        str(result.get("provider") or ""),
                        float(result.get("checked") or time.time()),
                        1 if result.get("malicious") else 0,
                        int(result.get("detections") or 0),
                        int(result.get("total") or 0),
                        str(result.get("file_name") or ""),
                        json.dumps(result.get("signatures") or [], ensure_ascii=False),
                        json.dumps(result.get("tags") or [], ensure_ascii=False),
                        json.dumps(result.get("raw") or {}, ensure_ascii=False),
                    ),
                )
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    # --------------------------------------------------------------- blocked IPs
    def add_blocked_ip(self, ip: str, reason: str = "") -> None:
        if self._conn is None or not ip:
            return
        try:
            with self._lock, self._conn:
                self._conn.execute(
                    """
                    INSERT INTO blocked_ips(ip, blocked_at, reason) VALUES (?, ?, ?)
                    ON CONFLICT(ip) DO UPDATE SET
                        blocked_at = excluded.blocked_at,
                        reason = excluded.reason
                    """,
                    (ip, time.time(), reason),
                )
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    def remove_blocked_ip(self, ip: str) -> None:
        if self._conn is None or not ip:
            return
        try:
            with self._lock, self._conn:
                self._conn.execute("DELETE FROM blocked_ips WHERE ip = ?", (ip,))
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    def blocked_ips(self) -> list[dict]:
        if self._conn is None:
            return []
        try:
            with self._lock:
                rows = self._conn.execute(
                    "SELECT ip, blocked_at, reason FROM blocked_ips ORDER BY blocked_at DESC"
                ).fetchall()
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return []
        return [
            {"ip": row["ip"], "when": float(row["blocked_at"] or 0.0), "reason": row["reason"] or ""}
            for row in rows
        ]

    def is_blocked_ip(self, ip: str) -> bool:
        return any(item["ip"] == ip for item in self.blocked_ips())

    @staticmethod
    def _load_list(value: str) -> list[str]:
        try:
            data = json.loads(value or "[]")
        except json.JSONDecodeError:
            return []
        return [str(item) for item in data] if isinstance(data, list) else []

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                finally:
                    self._conn = None
