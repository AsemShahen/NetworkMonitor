from __future__ import annotations

"""SQLite storage for monthly and daily per-application usage.

The GUI and a future headless collector can read the same database.  WAL mode
and a process-local lock keep the current single-process writer safe while the
UI reads from the main thread.
"""

import calendar
import csv
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import USAGE_DB


class UsageStore:
    def __init__(self, path: Path = USAGE_DB):
        self.path = Path(path)
        self._lock = threading.RLock()
        self.last_error: str | None = None
        self._conn: sqlite3.Connection | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.last_error = str(exc)
            return
        self._connect()

    def _connect(self) -> None:
        try:
            self._conn = sqlite3.connect(
                str(self.path),
                timeout=5.0,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            with self._lock:
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA synchronous=NORMAL")
                self._conn.execute("PRAGMA busy_timeout=5000")
                self._conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS apps (
                        app_key TEXT PRIMARY KEY,
                        name TEXT NOT NULL DEFAULT '',
                        exe TEXT NOT NULL DEFAULT '',
                        first_seen REAL NOT NULL DEFAULT 0,
                        last_seen REAL NOT NULL DEFAULT 0
                    );
                    CREATE TABLE IF NOT EXISTS monthly (
                        month TEXT NOT NULL,
                        app_key TEXT NOT NULL,
                        down INTEGER NOT NULL DEFAULT 0,
                        up INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (month, app_key)
                    );
                    CREATE TABLE IF NOT EXISTS daily (
                        day TEXT NOT NULL,
                        app_key TEXT NOT NULL,
                        down INTEGER NOT NULL DEFAULT 0,
                        up INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (day, app_key)
                    );
                    CREATE INDEX IF NOT EXISTS idx_monthly_month ON monthly(month);
                    CREATE INDEX IF NOT EXISTS idx_daily_day ON daily(day);
                    """
                )
                self._conn.commit()
        except (OSError, sqlite3.Error) as exc:
            self.last_error = str(exc)
            self._conn = None

    @staticmethod
    def _segments(start: float, end: float) -> list[tuple[float, float]]:
        """Split an interval at local midnight and month boundaries."""
        if end <= start:
            return [(end, 1.0)]
        # A very long interval usually means suspend/resume.  Attributing it to
        # the current bucket is safer than spreading it across past months.
        if end - start > 3600:
            return [(end, 1.0)]
        span = end - start
        segments: list[tuple[float, float]] = []
        cursor = start
        guard = 0
        while cursor < end and guard < 400:
            guard += 1
            dt = datetime.fromtimestamp(cursor)
            day_end = datetime(dt.year, dt.month, dt.day) + timedelta(days=1)
            if dt.month == 12:
                month_end = datetime(dt.year + 1, 1, 1)
            else:
                month_end = datetime(dt.year, dt.month + 1, 1)
            segment_end = min(end, day_end.timestamp(), month_end.timestamp())
            if segment_end <= cursor:
                segment_end = min(end, cursor + 1.0)
            fraction = max(0.0, (segment_end - cursor) / span)
            segments.append((cursor, fraction))
            cursor = segment_end
        if not segments:
            return [(end, 1.0)]
        total = sum(fraction for _, fraction in segments)
        if total > 0 and abs(total - 1.0) > 0.0001:
            segments[-1] = (segments[-1][0], segments[-1][1] + (1.0 - total))
        return segments

    def add_interval(
        self,
        app_key: str,
        name: str,
        exe: str,
        down: int,
        up: int,
        start: float,
        end: float,
    ) -> None:
        if not app_key or (down <= 0 and up <= 0):
            return
        if self._conn is None:
            return
        segments = self._segments(start, end)
        daily: dict[str, list[int]] = {}
        monthly: dict[str, list[int]] = {}
        allocated_down = 0
        allocated_up = 0
        for index, (ts, fraction) in enumerate(segments):
            moment = datetime.fromtimestamp(ts)
            day_key = moment.strftime("%Y-%m-%d")
            month_key = moment.strftime("%Y-%m")
            if index == len(segments) - 1:
                d_down = max(0, down - allocated_down)
                d_up = max(0, up - allocated_up)
            else:
                d_down = int(down * fraction)
                d_up = int(up * fraction)
            allocated_down += d_down
            allocated_up += d_up
            daily.setdefault(day_key, [0, 0])
            monthly.setdefault(month_key, [0, 0])
            daily[day_key][0] += d_down
            daily[day_key][1] += d_up
            monthly[month_key][0] += d_down
            monthly[month_key][1] += d_up
        try:
            with self._lock, self._conn:
                now = max(start, end) or time.time()
                self._conn.execute(
                    """
                    INSERT INTO apps(app_key, name, exe, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(app_key) DO UPDATE SET
                        name = CASE WHEN excluded.name <> '' THEN excluded.name ELSE apps.name END,
                        exe = CASE WHEN excluded.exe <> '' THEN excluded.exe ELSE apps.exe END,
                        first_seen = CASE WHEN apps.first_seen = 0 THEN excluded.first_seen ELSE apps.first_seen END,
                        last_seen = MAX(apps.last_seen, excluded.last_seen)
                    """,
                    (app_key, name or "", exe or "", min(start, end) or now, now),
                )
                for day_key, values in daily.items():
                    self._conn.execute(
                        """
                        INSERT INTO daily(day, app_key, down, up) VALUES (?, ?, ?, ?)
                        ON CONFLICT(day, app_key) DO UPDATE SET
                            down = daily.down + excluded.down,
                            up = daily.up + excluded.up
                        """,
                        (day_key, app_key, values[0], values[1]),
                    )
                for month_key, values in monthly.items():
                    self._conn.execute(
                        """
                        INSERT INTO monthly(month, app_key, down, up) VALUES (?, ?, ?, ?)
                        ON CONFLICT(month, app_key) DO UPDATE SET
                            down = monthly.down + excluded.down,
                            up = monthly.up + excluded.up
                        """,
                        (month_key, app_key, values[0], values[1]),
                    )
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    def month_totals(self, month: str) -> tuple[int, int]:
        if self._conn is None:
            return 0, 0
        try:
            with self._lock:
                row = self._conn.execute(
                    "SELECT COALESCE(SUM(down),0) AS d, COALESCE(SUM(up),0) AS u "
                    "FROM monthly WHERE month = ?",
                    (month,),
                ).fetchone()
            return int(row["d"] or 0), int(row["u"] or 0)
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return 0, 0

    def monthly(self, month: str) -> list[dict]:
        if self._conn is None:
            return []
        try:
            with self._lock:
                rows = self._conn.execute(
                    """
                    SELECT m.app_key, COALESCE(a.name, '') AS name,
                           COALESCE(a.exe, '') AS exe, m.down, m.up,
                           COALESCE(a.last_seen, 0) AS last_seen
                    FROM monthly m
                    LEFT JOIN apps a ON a.app_key = m.app_key
                    WHERE m.month = ?
                    ORDER BY (m.down + m.up) DESC, name COLLATE NOCASE
                    """,
                    (month,),
                ).fetchall()
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return []
        result = []
        for row in rows:
            down = int(row["down"] or 0)
            up = int(row["up"] or 0)
            result.append(
                {
                    "app_key": row["app_key"],
                    "name": row["name"] or row["app_key"],
                    "exe": row["exe"] or "",
                    "down": down,
                    "up": up,
                    "total": down + up,
                    "last_seen": float(row["last_seen"] or 0),
                }
            )
        return result

    def daily(self, month: str) -> list[dict]:
        """Return one row for every day in the month, including empty days."""
        try:
            year, month_number = (int(part) for part in month.split("-", 1))
            days_in_month = calendar.monthrange(year, month_number)[1]
        except (ValueError, TypeError):
            return []
        if self._conn is None:
            return []
        try:
            with self._lock:
                rows = self._conn.execute(
                    """
                    SELECT day, COALESCE(SUM(down),0) AS d, COALESCE(SUM(up),0) AS u
                    FROM daily
                    WHERE day LIKE ?
                    GROUP BY day
                    """,
                    (f"{month}-%",),
                ).fetchall()
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return []
        by_day = {row["day"]: (int(row["d"] or 0), int(row["u"] or 0)) for row in rows}
        result = []
        for day_number in range(1, days_in_month + 1):
            day_key = f"{month}-{day_number:02d}"
            down, up = by_day.get(day_key, (0, 0))
            result.append({"day": day_key, "down": down, "up": up, "total": down + up})
        return result

    def months(self) -> list[str]:
        current = datetime.now().strftime("%Y-%m")
        if self._conn is None:
            return [current]
        try:
            with self._lock:
                rows = self._conn.execute(
                    "SELECT DISTINCT month FROM monthly ORDER BY month DESC"
                ).fetchall()
        except sqlite3.Error as exc:
            self.last_error = str(exc)
            return [current]
        values = [row["month"] for row in rows]
        if current not in values:
            values.insert(0, current)
        return values

    def reset_month(self, month: str) -> None:
        if self._conn is None:
            return
        try:
            with self._lock, self._conn:
                self._conn.execute("DELETE FROM monthly WHERE month = ?", (month,))
                self._conn.execute("DELETE FROM daily WHERE day LIKE ?", (f"{month}-%",))
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    def prune(self, months: int = 24, days: int = 90) -> None:
        if self._conn is None:
            return
        today = date.today()
        month_index = today.year * 12 + (today.month - 1) - max(1, months)
        cutoff_month = f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"
        cutoff_day = (today - timedelta(days=max(1, days))).isoformat()
        try:
            with self._lock, self._conn:
                self._conn.execute("DELETE FROM monthly WHERE month < ?", (cutoff_month,))
                self._conn.execute("DELETE FROM daily WHERE day < ?", (cutoff_day,))
        except sqlite3.Error as exc:
            self.last_error = str(exc)

    def export_csv(self, path: Path, month: str) -> int:
        rows = self.monthly(month)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "month",
                    "app_key",
                    "application",
                    "executable",
                    "download_bytes",
                    "upload_bytes",
                    "total_bytes",
                    "last_seen",
                ]
            )
            for row in rows:
                last_seen = ""
                if row["last_seen"]:
                    last_seen = datetime.fromtimestamp(row["last_seen"]).isoformat(timespec="seconds")
                writer.writerow(
                    [
                        month,
                        row["app_key"],
                        row["name"],
                        row["exe"],
                        row["down"],
                        row["up"],
                        row["total"],
                        last_seen,
                    ]
                )
            total_down = sum(row["down"] for row in rows)
            total_up = sum(row["up"] for row in rows)
            writer.writerow(
                ["TOTAL", "", "", "", total_down, total_up, total_down + total_up, ""]
            )
        return len(rows)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                finally:
                    self._conn = None
