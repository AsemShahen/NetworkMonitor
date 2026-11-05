from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from netmon.collectors.net_conn import SocketRecord, app_key_for, cgroup_app_key
from netmon.collectors.netlink import NetlinkBackend
from netmon.collectors.traffic import TrafficEngine, parse_ss, parse_ss_sockets
from netmon.config import BlocklistStore, ConfigStore, slugify
from netmon.controller import Controller
from netmon.i18n import get_language, refresh_label, set_language, tr
from netmon.models import BlockEntry
from netmon.usage import UsageStore
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

SS_MIXED = """State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
ESTAB  0      0      10.0.0.5:52344      142.250.0.1:443 users:(("lm-studio",pid=30832,fd=15)) ino:4242 cgroup:/user.slice/app-flatpak-ai.lmstudio.lm\\x2dstudio-123.scope
\t bytes_sent:1200 bytes_received:45000
"""

SS_UDP = """State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
UNCONN 0      0      0.0.0.0:5353        0.0.0.0:*     users:(("lm-studio",pid=30832,fd=16)) ino:4243 cgroup:/user.slice/app-flatpak-ai.lmstudio.lm\\x2dstudio-123.scope
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

    def test_per_socket_records_keep_inode_and_cgroup(self) -> None:
        tcp = parse_ss_sockets(SS_MIXED, udp=False)
        self.assertEqual(len(tcp), 1)
        self.assertEqual(tcp[0].inode, 4242)
        self.assertEqual(tcp[0].pids, [30832])
        self.assertTrue(tcp[0].measured)
        self.assertIn("lmstudio", tcp[0].cgroup)

        udp = parse_ss_sockets(SS_UDP, udp=True)
        self.assertEqual(len(udp), 1)
        self.assertFalse(udp[0].measured)
        self.assertEqual(udp[0].inode, 4243)
        self.assertEqual(udp[0].pids, [30832])


class _Slot:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class TestNetlinkParsing(unittest.TestCase):
    def test_nla_slots_are_decoded(self) -> None:
        info = {"tcpi_bytes_sent": 1200, "tcpi_bytes_received": 5000}
        message = {
            "attrs": [
                _Slot("INET_DIAG_CGROUP_ID", 1234),
                _Slot("INET_DIAG_INFO", info),
            ]
        }
        attrs = NetlinkBackend._attrs(message)
        self.assertEqual(attrs["INET_DIAG_CGROUP_ID"], 1234)
        self.assertEqual(attrs["INET_DIAG_INFO"], info)
        self.assertEqual(NetlinkBackend._tcp_counters(info), (1200, 5000, True))


class TestEngineFallback(unittest.TestCase):
    def test_netlink_is_preferred(self) -> None:
        engine = TrafficEngine()
        record = SocketRecord(inode=1, protocol="tcp", measured=True)
        engine._netlink.poll = lambda: ([record], None)
        records, source, error, _, _ = engine._collect()
        self.assertEqual(source, "netlink")
        self.assertEqual(records, [record])
        self.assertIsNone(error)

    def test_ss_then_proc_fallback(self) -> None:
        engine = TrafficEngine()
        record = SocketRecord(inode=2, protocol="tcp", measured=True)
        engine._netlink.poll = lambda: ([], "netlink unavailable")
        engine._ss.poll = lambda: ([record], None)
        records, source, _, netlink_error, ss_error = engine._collect()
        self.assertEqual(source, "ss")
        self.assertEqual(records, [record])
        self.assertEqual(netlink_error, "netlink unavailable")
        self.assertIsNone(ss_error)

        engine._ss.poll = lambda: ([], "ss unavailable")
        engine._proc.poll = lambda: []
        _, source, error, _, _ = engine._collect()
        self.assertEqual(source, "proc-net")
        self.assertTrue(error)


class TestIdentity(unittest.TestCase):
    def test_flatpak_and_snap_cgroups(self) -> None:
        key, name = cgroup_app_key(
            "/user.slice/app-flatpak-ai.lmstudio.lm\\x2dstudio-3422534380.scope"
        )
        self.assertEqual(key, "flatpak:ai.lmstudio.lm-studio")
        self.assertEqual(name, "LM Studio")
        key, name = cgroup_app_key("/user.slice/snap.firefox.firefox-123.scope")
        self.assertEqual(key, "snap:firefox")
        self.assertEqual(name, "Firefox")

    def test_appimage_uses_outer_file(self) -> None:
        key, name = app_key_for(
            "/tmp/.mount_Foo/usr/bin/foo",
            cmdline="/home/user/Apps/Foo.AppImage --flag",
        )
        self.assertEqual(key, "appimage:Foo.AppImage")
        self.assertEqual(name, "Foo")


class TestFormatting(unittest.TestCase):
    def test_fmt_rate(self) -> None:
        self.assertIn("KB/s", fmt_rate(1500))
        self.assertIn("MB/s", fmt_rate(2_500_000))
        self.assertTrue(fmt_rate(0).startswith("0"))

    def test_pretty_name_word_boundary(self) -> None:
        self.assertEqual(pretty_name("waterfox-bin", "/opt/waterfox/waterfox-bin"), "Waterfox")
        self.assertEqual(pretty_name("ai.opencode.des", "/app/ai.opencode.desktop"), "ai.opencode.des")
        self.assertEqual(pretty_name("code", "/usr/bin/code"), "code")

    def test_lm_studio_name(self) -> None:
        self.assertEqual(pretty_name("lm-studio", "/app/lm-studio"), "LM Studio")


class TestI18n(unittest.TestCase):
    def tearDown(self) -> None:
        set_language("en")

    def test_default_english_and_switch(self) -> None:
        set_language("en")
        self.assertEqual(get_language(), "en")
        self.assertEqual(tr("tab.live"), "Live")
        set_language("ar")
        self.assertEqual(get_language(), "ar")
        self.assertEqual(tr("tab.live"), "الرصد المباشر")

    def test_interval_labels(self) -> None:
        set_language("en")
        self.assertEqual(refresh_label(30000), "30 seconds")
        set_language("ar")
        self.assertEqual(refresh_label(30000), "30 ثانية")

    def test_usage_labels_exist_in_both_languages(self) -> None:
        for code in ("en", "ar"):
            set_language(code)
            self.assertTrue(tr("tab.usage"))
            self.assertNotEqual(tr("usage.note", count=2), "usage.note")
            self.assertNotEqual(tr("usage.col.total"), "usage.col.total")


class TestStores(unittest.TestCase):
    def test_config_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = ConfigStore(path)
            self.assertEqual(cfg.get("refresh_ms"), 30000)
            self.assertEqual(cfg.get("language"), "en")
            cfg.set("refresh_ms", 5000)
            self.assertTrue(path.exists())
            again = ConfigStore(path)
            self.assertEqual(again.get("refresh_ms"), 5000)
            self.assertTrue(again.get("keep_usage"))
            self.assertTrue(again.get("group_cgroups"))
            self.assertEqual(again.get("recent_seconds"), 300)
            self.assertFalse(again.get("minimize_to_tray"))

    def test_blocklist_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blocklist.json"
            store = BlocklistStore(path)
            entry = BlockEntry(
                slug=slugify("/opt/waterfox/waterfox-bin"),
                name="Waterfox",
                exe="/opt/waterfox/waterfox-bin",
            )
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


class TestUsageStore(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "usage.db"
        self.store = UsageStore(self.path)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    @staticmethod
    def _ts(*args) -> float:
        return datetime(*args).timestamp()

    def test_month_and_day_totals(self) -> None:
        start = self._ts(2024, 1, 15, 12, 0, 0)
        end = self._ts(2024, 1, 15, 12, 0, 10)
        self.store.add_interval("exe:/usr/bin/app", "App", "/usr/bin/app", 1000, 400, start, end)
        self.assertEqual(self.store.month_totals("2024-01"), (1000, 400))
        rows = self.store.monthly("2024-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["app_key"], "exe:/usr/bin/app")
        self.assertEqual(rows[0]["name"], "App")
        daily = {row["day"]: row for row in self.store.daily("2024-01")}
        self.assertEqual(len(daily), 31)
        self.assertEqual(daily["2024-01-15"]["total"], 1400)
        self.assertEqual(daily["2024-01-01"]["total"], 0)

    def test_cross_month_split(self) -> None:
        start = self._ts(2024, 1, 31, 23, 59, 50)
        end = self._ts(2024, 2, 1, 0, 0, 10)
        self.store.add_interval("exe:/app", "App", "/app", 100, 20, start, end)
        self.assertEqual(self.store.month_totals("2024-01"), (50, 10))
        self.assertEqual(self.store.month_totals("2024-02"), (50, 10))

    def test_export_and_reset(self) -> None:
        start = self._ts(2024, 3, 4, 10, 0, 0)
        end = self._ts(2024, 3, 4, 10, 0, 5)
        self.store.add_interval("flatpak:org.example.App", "Example", "/app", 1234, 567, start, end)
        out = Path(self.tmp.name) / "usage.csv"
        count = self.store.export_csv(out, "2024-03")
        self.assertEqual(count, 1)
        text = out.read_text(encoding="utf-8-sig")
        self.assertIn("flatpak:org.example.App", text)
        self.assertIn("1234", text)
        self.assertIn("TOTAL", text)
        self.store.reset_month("2024-03")
        self.assertEqual(self.store.month_totals("2024-03"), (0, 0))

    def test_prune_removes_old_months(self) -> None:
        start = self._ts(2020, 1, 1, 0, 0, 0)
        end = self._ts(2020, 1, 1, 0, 0, 10)
        self.store.add_interval("exe:/old", "Old", "/old", 10, 0, start, end)
        self.store.prune(months=24, days=90)
        self.assertEqual(self.store.month_totals("2020-01"), (0, 0))

    def test_merge_group_uses_unique_exe_totals(self) -> None:
        base = {
            "pid": 1,
            "name": "LM Studio",
            "exe": "/app/lm-studio",
            "cmdline": "",
            "uid": 1000,
            "state": "S",
            "cpu": 0.0,
            "rss": 0,
            "down_bps": 10.0,
            "up_bps": 2.0,
            "conns": 2,
            "tcp_sockets": 2,
            "udp_sockets": 0,
            "udp_unmeasured": 0,
            "has_unmeasured": False,
            "blocked": False,
            "active": True,
            "idle": False,
            "pids": [1],
            "process_count": 1,
            "_exe_totals": {"/app/lm-studio": (100, 10)},
            "down_total": 100,
            "up_total": 10,
        }
        other = dict(base)
        other["pid"] = 2
        other["pids"] = [2]
        other["_exe_totals"] = {"/app/lm-studio": (100, 10)}
        Controller._merge_row(base, other)
        self.assertEqual(sorted(base["pids"]), [1, 2])
        self.assertEqual(base["down_total"], 100)
        self.assertEqual(base["up_total"], 10)
        self.assertEqual(base["process_count"], 2)


if __name__ == "__main__":
    unittest.main()
