from __future__ import annotations
import os
from collections import defaultdict

def inode_to_pids():
    m = defaultdict(list)
    for pid in os.listdir('/proc'):
        if not pid.isdigit(): continue
        fd = f'/proc/{pid}/fd'
        try:
            for f in os.listdir(fd):
                try:
                    l = os.readlink(fd+'/'+f)
                    if l.startswith('socket:['):
                        ino = int(l[8:-1])
                        m[ino].append(int(pid))
                except: pass
        except: pass
    return m

def get_active_pids():
    imap = inode_to_pids()
    pids = set()
    # tcp
    for path in ['/proc/net/tcp','/proc/net/tcp6','/proc/net/udp','/proc/net/udp6']:
        try:
            with open(path) as f:
                for l in f.readlines()[1:]:
                    parts = l.split()
                    if len(parts) < 10: continue
                    st = parts[3]
                    inode = int(parts[9])
                    # ESTABLISHED etc
                    if st in ('01','02'):  # ESTAB, SYN_SENT? show active
                        for pid in imap.get(inode, []):
                            pids.add(pid)
        except: pass
    return pids
