from __future__ import annotations

"""QThread workers for reputation lookups and on-demand file hashing."""

from PySide6.QtCore import QThread, Signal

from ..security.cache import FILE_CACHE_SECONDS, IP_CACHE_SECONDS, SecurityStore
from ..security.file_reputation import check_file_hash, sha256_file
from ..security.ip_reputation import check_ip


class IPReputationThread(QThread):
    result_ready = Signal(object)
    progress = Signal(int, int, str)

    def __init__(
        self,
        ips: list[str],
        provider: str,
        api_key: str,
        store: SecurityStore,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ips = list(ips)
        self.provider = provider
        self.api_key = api_key
        self.store = store

    def _sleep(self, seconds: float) -> None:
        remaining = max(0.0, seconds)
        while remaining > 0 and not self.isInterruptionRequested():
            chunk = min(0.25, remaining)
            self.msleep(int(chunk * 1000))
            remaining -= chunk

    def run(self) -> None:  # noqa: D401 - QThread entry point
        results: list[dict] = []
        total = len(self.ips)
        # VirusTotal's free tier allows roughly four requests per minute.
        delay = 16.0 if self.provider == "virustotal" else 0.6
        for index, ip in enumerate(self.ips, start=1):
            if self.isInterruptionRequested():
                break
            cached = self.store.get_ip(ip, self.provider, max_age=IP_CACHE_SECONDS)
            if cached is not None:
                results.append(cached)
                self.progress.emit(index, total, ip)
                continue
            result = check_ip(ip, self.provider, self.api_key)
            if self.isInterruptionRequested():
                break
            if result.get("ok"):
                self.store.put_ip(result)
            results.append(result)
            self.progress.emit(index, total, ip)
            if index < total:
                self._sleep(delay)
        self.result_ready.emit(results)


class FileHashThread(QThread):
    result_ready = Signal(object)

    def __init__(
        self,
        path: str,
        provider: str,
        api_key: str,
        store: SecurityStore,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.path = path
        self.provider = provider
        self.api_key = api_key
        self.store = store

    def run(self) -> None:  # noqa: D401 - QThread entry point
        result: dict
        if self.isInterruptionRequested():
            return
        try:
            digest = sha256_file(self.path, should_stop=self.isInterruptionRequested)
        except InterruptedError:
            return
        except (OSError, ValueError) as exc:
            result = {
                "path": self.path,
                "sha256": "",
                "provider": self.provider,
                "ok": False,
                "error_key": "security.error.hash_read",
                "error_args": {"message": str(exc)},
                "error": str(exc),
            }
            self.result_ready.emit(result)
            return
        if self.isInterruptionRequested():
            return
        cached = self.store.get_file(digest, self.provider, max_age=FILE_CACHE_SECONDS)
        if cached is not None:
            cached["path"] = self.path
            self.result_ready.emit(cached)
            return
        result = check_file_hash(self.path, digest, self.provider, self.api_key)
        if self.isInterruptionRequested():
            return
        if result.get("ok"):
            self.store.put_file(result)
        self.result_ready.emit(result)
