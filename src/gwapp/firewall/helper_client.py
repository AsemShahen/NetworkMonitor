from __future__ import annotations
import json, subprocess, os, sys
from pathlib import Path

class HelperClient:
    def _call(self, op, exe):
        try:
            helper = Path(__file__).resolve().parents[3] / "bin" / "glasswire-helper"
            if not helper.exists():
                helper = "/usr/local/bin/glasswire-helper"
            if not helper.exists():
                return False
            p = subprocess.run(["pkexec", str(helper)], input=json.dumps({"op":op,"exe":exe}), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if p.returncode != 0:
                return False
            try:
                r = json.loads(p.stdout)
                return bool(r.get("ok"))
            except Exception:
                return False
        except Exception:
            return False

    def block(self, exe: str) -> bool:
        return self._call("block", exe)

    def unblock(self, exe: str) -> bool:
        return self._call("unblock", exe)
