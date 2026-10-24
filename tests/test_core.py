from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from netmon.collectors.traffic import parse_ss
from netmon.config import BlocklistStore, ConfigStore, slugify
from netmon.models import BlockEntry
from netmon.util import fmt_rate, pretty_name


SS_TCP = """State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
ESTAB  0      0      10.0.0.5:52344      142.250.0.1:443 users:(("waterfox-bin",pid=3676,fd=234)) ino:9911 sk:1
\t skmem:(r0,rb131072,t0,tb2626560,f0,w0,o0,bl0,d0) ts sack cubic wscale:7,7 rto:204 rtt:1.5/0.7
\t bytes_sent:1200 bytes_received:45000
ESTAB  0      0      10.0.0.5:52350      142.250.0.2:443 users:(("waterfox-bin",pid=3676,fd=235)) ino:9912 sk:1
\t bytes_sent:300 bytes_acked:300 bytes_received:5000
ESTAB  0      0      10.0.0.5:41000      1.1.1.1:443 users:(("opera",pid=4000,fd=10)) ino:9913
\t bytes_sent:100 bytes_received:200
"""


class TestParseSS(unittest.TestCase):
    def test_aggregates_sockets_per_pid(self) -> None:
        counters = parse_ss(SS_TCP)
        self.assertEqual(set(counters), {3676, 4000})
        wf = counters[3676]
        self.assertEqual(wf.name, "waterfox-bin")
        self.assertEqual(wf.tx, 1500)
        self.assertEqual(wf.rx, 50000)
        self.assertEqual(wf.sockets, 2)
        self.assertEqual(counters[4000].rx, 200)

    def test_empty(self) -> None:
        self.assertEqual(parse_ss(""), {})

    def test_listen_sockets_are_ignored(self) -> None:
        text = """State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      128    0.0.0.0:22            0.0.0.0:*     users:(("sshd",pid=700,fd=3)) ino:77 sk:1
ESTAB  0      0      10.0.0.5:50000       1.1.1.1:443   users:(("firefox",pid=701,fd=8)) ino:78 sk:2
\t bytes_sent:10 bytes_received:20
"""
        counters = parse_ss(text)
        self.assertNotIn(700, counters)
        self.assertIn(701, counters)


class TestFormatting(unittest.TestCase):
    def test_fmt_rate(self) -> None:
        self.assertIn("KB/s", fmt_rate(1500))
        self.assertIn("MB/s", fmt_rate(2_500_000))
        self.assertTrue(fmt_rate(0).startswith("0"))

    def test_pretty_name_word_boundary(self) -> None:
        self.assertEqual(pretty_name("waterfox-bin", "/opt/waterfox/waterfox-bin"), "Waterfox")
        self.assertEqual(pretty_name("ai.opencode.des", "/app/ai.opencode.desktop"), "ai.opencode.des")
        self.assertEqual(pretty_name("code", "/usr/bin/code"), "code")


class TestStores(unittest.TestCase):
    def test_config_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = ConfigStore(path)
            self.assertEqual(cfg.get("refresh_ms"), 30000)
            cfg.set("refresh_ms", 5000)
            self.assertTrue(path.exists())
            again = ConfigStore(path)
            self.assertEqual(again.get("refresh_ms"), 5000)

    def test_blocklist_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blocklist.json"
            store = BlocklistStore(path)
            entry = BlockEntry(slug=slugify("/opt/waterfox/waterfox-bin"), name="Waterfox", exe="/opt/waterfox/waterfox-bin")
            store.add(entry)
            store2 = BlocklistStore(path)
            self.assertTrue(store2.has(entry.slug))
            self.assertTrue(store2.remove(entry.slug))

    def test_export_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blocklist.json"
            out = Path(tmp) / "export.txt"
            store = BlocklistStore(path)
            store.add(BlockEntry(slug="abc", name="Waterfox", exe="/opt/waterfox/waterfox-bin"))
            store.export_to(out)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)


if __name__ == "__main__":
    unittest.main()
