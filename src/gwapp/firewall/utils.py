from __future__ import annotations

import hashlib
import os

def slug_exe(exe: str) -> str:
    if not exe:
        return "unknown"
    base = os.path.basename(exe.rstrip("/")) or "unknown"
    h = hashlib.sha256(exe.encode("utf-8", errors="ignore")).hexdigest()[:8]
    clean = "".join(c if c.isalnum() or c in "._-" else "_" for c in base)
    return f"{clean}-{h}" if clean else h