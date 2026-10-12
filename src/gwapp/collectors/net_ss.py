from __future__ import annotations
import subprocess
import os

def get_net_by_pid() -> dict:
    d = {}
    try:
        p = subprocess.run(['ss','-tupn'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        for line in p.stdout.splitlines():
            if 'users:' in line:
                try:
                    part = line.split('users:',1)[1]
                    if 'pid=' in part:
                        pid = int(part.split('pid=')[1].split(',')[0])
                        name = part.split('pid=')[0].replace('(','').replace('"','')
                        if name.endswith(','): name = name[:-1]
                        if name == '': name = part
                        d.setdefault(pid, {'name': name, 'conns': 0})
                        d[pid]['conns'] += 1
                except Exception:
                    pass
    except Exception:
        pass
    return d
