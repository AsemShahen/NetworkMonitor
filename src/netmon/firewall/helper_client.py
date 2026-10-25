from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ..i18n import get_language, tr


def find_helper() -> str | None:
    env = os.environ.get("NETWORK_MONITOR_HELPER")
    if env and Path(env).exists():
        return env
    candidates = [
        Path("/usr/libexec/network-monitor/network-monitor-helper"),
        Path("/usr/local/bin/network-monitor-helper"),
        Path("/usr/bin/network-monitor-helper"),
        Path(__file__).resolve().parents[3] / "bin" / "network-monitor-helper",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


class HelperClient:
    """عميل يستدعي المساعد المميز (root) عبر pkexec لعمليات الحظر."""

    def __init__(self) -> None:
        self.helper = find_helper()
        self.last_error = ""

    def _call(self, payload: dict, timeout: int = 120) -> dict:
        payload = {**payload, "lang": get_language()}
        if not self.helper:
            return {"ok": False, "error": tr("helper.not_found")}
        runner = [self.helper] if os.access(self.helper, os.X_OK) else [sys.executable, self.helper]
        if os.geteuid() == 0:
            cmd = runner
        else:
            pkexec = shutil.which("pkexec")
            if not pkexec:
                return {"ok": False, "error": tr("helper.pkexec_missing")}
            cmd = [pkexec, *runner]
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(payload, ensure_ascii=False),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": tr("helper.timeout")}
        except OSError as exc:
            return {"ok": False, "error": tr("helper.oserror", error=exc)}

        if proc.returncode != 0:
            err = (proc.stderr or "").strip() or tr("helper.failed", code=proc.returncode)
            return {"ok": False, "error": err}
        try:
            data = json.loads(proc.stdout.strip() or "{}")
        except json.JSONDecodeError:
            return {"ok": False, "error": tr("helper.bad_json")}
        if not isinstance(data, dict):
            return {"ok": False, "error": tr("helper.unexpected")}
        return data

    def block(self, exe: str, name: str = "") -> tuple[bool, str]:
        r = self._call({"op": "block", "exe": exe, "name": name})
        return bool(r.get("ok")), str(r.get("error") or "")

    def unblock(self, exe: str) -> tuple[bool, str]:
        r = self._call({"op": "unblock", "exe": exe})
        return bool(r.get("ok")), str(r.get("error") or "")

    def apply(self, entries: list[dict]) -> tuple[bool, str]:
        r = self._call({"op": "apply", "entries": entries})
        return bool(r.get("ok")), str(r.get("error") or "")

    def status(self) -> dict:
        return self._call({"op": "status"}, timeout=60)
