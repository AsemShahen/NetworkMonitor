from __future__ import annotations

import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def build_inode_map(cache_ttl: float = 5.0) -> Dict[int, List[int]]:
    """بناء خريطة inode -> قائمة PIDs التي تملك هذا المقبس."""
    m: Dict[int, List[int]] = defaultdict(list)
    for pid_str in os.listdir("/proc"):
        if not pid_str.isdigit():
            continue
        pid = int(pid_str)
        fd_dir = Path(f"/proc/{pid}/fd")
        try:
            for fd in fd_dir.iterdir():
                try:
                    lnk = os.readlink(fd)
                    if lnk.startswith("socket:["):
                        inode = int(lnk[8:-1])
                        m[inode].append(pid)
                except Exception:
                    continue
        except Exception:
            continue
    return m