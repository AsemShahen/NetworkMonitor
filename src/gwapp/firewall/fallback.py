from __future__ import annotations
import os, subprocess

class FallbackBlocker:
    def block(self, exe: str) -> bool:
        # try simple nftables rule placeholder (user may need sudo)
        return False

    def unblock(self, exe: str) -> bool:
        return False
