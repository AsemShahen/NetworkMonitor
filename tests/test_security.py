from __future__ import annotations

import json
import socket
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from netmon.collectors.net_conn import (
    SocketRecord,
    format_netlink_address,
    format_netlink_port,
    split_endpoint,
)
from netmon.collectors.traffic import parse_ss_sockets
from netmon.config import ConfigStore
from netmon.i18n import set_language, tr
from netmon.security.cache import SecurityStore
from netmon.security.file_reputation import sha256_file
from netmon.security.heuristics import (
    SecurityEngine,
    is_public_ip,
    is_suspicious_executable,
)
from netmon.security.ip_reputation import check_ip


class _FakeResponse:
    def __init__(self, data: dict) -> None:
        self._body = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self._body


class TestEndpointParsing(unittest.TestCase):
    def test_split_endpoint_ipv4_ipv6_and_wildcard(self) -> None:
        self.assertEqual(split_endpoint("142.250.0.1:443"), ("142.250.0.1", 443))
        self.assertEqual(split_endpoint("[2001:db8::1]:4444"), ("2001:db8::1", 4444))
        self.assertEqual(split_endpoint("0.0.0.0:*"), ("", 0))
        self.assertEqual(split_endpoint("*:*"), ("", 0))

    def test_ss_parser_keeps_remote_endpoint(self) -> None:
        text = """State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
ESTAB  0      0      10.0.0.5:52344      142.250.0.1:443 users:(("app",pid=123,fd=8)) ino:99
\t bytes_sent:10 bytes_received:20
"""
        records = parse_ss_sockets(text)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].remote_addr, "142.250.0.1")
        self.assertEqual(records[0].remote_port, 443)
        self.assertEqual(records[0].local_addr, "10.0.0.5")
        self.assertEqual(records[0].local_port, 52344)

    def test_netlink_address_and_port_helpers(self) -> None:
        self.assertEqual(format_netlink_address(socket.inet_aton("8.8.4.4"), socket.AF_INET), "8.8.4.4")
        self.assertEqual(format_netlink_port(443), 443)
        self.assertEqual(format_netlink_port(b"\x01\xbb"), 443)


class TestHeuristics(unittest.TestCase):
    def _row(self, **overrides) -> dict:
        row = {
            "pid": 123,
            "pids": [123],
            "app_key": "exe:/tmp/evil",
            "name": "evil",
            "exe": "/tmp/evil",
            "cmdline": "/tmp/evil",
            "up_bps": 0.0,
        }
        row.update(overrides)
        return row

    def test_temp_path_and_appimage_exception(self) -> None:
        self.assertTrue(is_suspicious_executable("/tmp/evil"))
        self.assertTrue(is_suspicious_executable("/var/tmp/evil"))
        self.assertTrue(is_suspicious_executable("/dev/shm/evil"))
        self.assertFalse(
            is_suspicious_executable(
                "/tmp/.mount_Foo/usr/bin/foo",
                "/home/user/Apps/Foo.AppImage --flag",
            )
        )

    def test_public_ip(self) -> None:
        self.assertTrue(is_public_ip("8.8.8.8"))
        self.assertFalse(is_public_ip("127.0.0.1"))
        self.assertFalse(is_public_ip("192.168.1.10"))
        self.assertFalse(is_public_ip("::1"))
        self.assertFalse(is_public_ip("not-an-ip"))

    def test_mining_port_and_external_ip_report(self) -> None:
        engine = SecurityEngine()
        socket_record = SocketRecord(
            inode=1,
            protocol="tcp",
            pids=[123],
            remote_addr="8.8.8.8",
            remote_port=4444,
            measured=True,
        )
        report = engine.analyze(
            [self._row()],
            [socket_record],
            upload_check=False,
            now=100.0,
        )
        kinds = {finding["kind"] for finding in report["findings"]}
        self.assertIn("temp_path", kinds)
        self.assertIn("mining_port", kinds)
        self.assertEqual(report["external_ips"][0]["ip"], "8.8.8.8")
        self.assertEqual(report["counts"]["critical"], 1)

    def test_local_mining_port_is_ignored(self) -> None:
        engine = SecurityEngine()
        socket_record = SocketRecord(
            inode=1,
            protocol="tcp",
            pids=[123],
            remote_addr="127.0.0.1",
            remote_port=4444,
            measured=True,
        )
        report = engine.analyze(
            [self._row(exe="/usr/bin/app", app_key="exe:/usr/bin/app")],
            [socket_record],
            path_check=False,
            upload_check=False,
            now=100.0,
        )
        self.assertNotIn("mining_port", {item["kind"] for item in report["findings"]})

    def test_upload_spike_needs_a_baseline(self) -> None:
        engine = SecurityEngine()
        row = self._row(exe="/usr/bin/backup", app_key="exe:/usr/bin/backup", up_bps=1024.0)
        engine.analyze([row], [], path_check=False, mining_check=False, now=100.0)
        row["up_bps"] = 20 * 1024 * 1024
        report = engine.analyze(
            [row],
            [],
            path_check=False,
            mining_check=False,
            spike_bps=5 * 1024 * 1024,
            spike_ratio=2.0,
            now=110.0,
        )
        kinds = {finding["kind"] for finding in report["findings"]}
        self.assertIn("upload_spike", kinds)

    def test_history_is_pruned(self) -> None:
        engine = SecurityEngine()
        row = self._row()
        engine.analyze([row], [], upload_check=False, now=100.0)
        self.assertTrue(engine.analyze([], [], now=2000.0)["findings"] == [])


class TestSecurityStore(unittest.TestCase):
    def test_ip_file_and_blocked_ip_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SecurityStore(Path(tmp) / "security.db")
            try:
                store.put_ip(
                    {
                        "ip": "8.8.8.8",
                        "provider": "abuseipdb",
                        "ok": True,
                        "score": 80,
                        "reports": 12,
                        "malicious": True,
                        "country": "US",
                        "isp": "Example",
                        "usage": "Data Center",
                        "checked": time.time(),
                    }
                )
                cached = store.get_ip("8.8.8.8", "abuseipdb", max_age=999999999)
                self.assertIsNotNone(cached)
                self.assertTrue(cached["cached"])
                self.assertTrue(cached["malicious"])
                self.assertEqual(cached["score"], 80)

                store.put_file(
                    {
                        "sha256": "a" * 64,
                        "provider": "malwarebazaar",
                        "ok": True,
                        "malicious": True,
                        "detections": 1,
                        "total": 1,
                        "file_name": "evil",
                        "signatures": ["AgentTesla"],
                        "tags": ["exe"],
                        "checked": time.time(),
                    }
                )
                file_result = store.get_file("a" * 64, "malwarebazaar", max_age=999999999)
                self.assertIsNotNone(file_result)
                self.assertEqual(file_result["signatures"], ["AgentTesla"])
                self.assertEqual(file_result["tags"], ["exe"])

                store.add_blocked_ip("8.8.8.8", "test")
                self.assertTrue(store.is_blocked_ip("8.8.8.8"))
                self.assertEqual(store.blocked_ips()[0]["ip"], "8.8.8.8")
                store.remove_blocked_ip("8.8.8.8")
                self.assertFalse(store.is_blocked_ip("8.8.8.8"))
            finally:
                store.close()


class TestFileHashing(unittest.TestCase):
    def test_sha256_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hello.bin"
            path.write_bytes(b"hello")
            self.assertEqual(
                sha256_file(str(path)),
                "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            )

    def test_sha256_file_can_be_interrupted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.bin"
            path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            calls = 0

            def should_stop() -> bool:
                nonlocal calls
                calls += 1
                return calls >= 2

            with self.assertRaises(InterruptedError):
                sha256_file(str(path), should_stop=should_stop)


class TestHelperIPSetParsing(unittest.TestCase):
    def test_blocked_ip_values_ignores_set_metadata(self) -> None:
        import importlib.util
        from importlib.machinery import SourceFileLoader

        root = Path(__file__).resolve().parents[1]
        loader = SourceFileLoader(
            "network_monitor_helper_test",
            str(root / "bin" / "network-monitor-helper"),
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        module.list_ip_set = lambda _name: """
            table inet network_monitor {
                set blocked_ips4 {
                    type ipv4_addr
                    size 65535
                    flags interval
                    elements = { 1.2.3.4, 5.6.7.8 }
                }
            }
        """
        self.assertEqual(module.blocked_ip_values(), ["1.2.3.4", "5.6.7.8"])


class TestIPReputationClient(unittest.TestCase):
    def test_abuseipdb_response_is_normalized(self) -> None:
        payload = {
            "data": {
                "abuseConfidenceScore": 75,
                "totalReports": 4,
                "countryCode": "DE",
                "isp": "Example ISP",
                "usageType": "Data Center",
            }
        }
        with mock.patch(
            "netmon.security.ip_reputation.urllib.request.urlopen",
            return_value=_FakeResponse(payload),
        ):
            result = check_ip("8.8.8.8", "abuseipdb", "key")
        self.assertTrue(result["ok"])
        self.assertTrue(result["malicious"])
        self.assertEqual(result["score"], 75)
        self.assertEqual(result["country"], "DE")
        self.assertEqual(result["provider"], "abuseipdb")

    def test_missing_key_is_reported_without_network(self) -> None:
        result = check_ip("8.8.8.8", "virustotal", "")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_key"], "security.error.no_api_key")


class TestConfigAndI18n(unittest.TestCase):
    def tearDown(self) -> None:
        set_language("en")

    def test_security_defaults_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = ConfigStore(Path(tmp) / "config.json")
            self.assertTrue(config.get("security_enabled"))
            self.assertEqual(config.get("security_ip_provider"), "abuseipdb")
            self.assertEqual(config.get("security_hash_provider"), "malwarebazaar")
            config.set("security_ip_provider", "bad")
            config.set("security_spike_mbps", "bad")
            again = ConfigStore(Path(tmp) / "config.json")
            self.assertEqual(again.get("security_ip_provider"), "abuseipdb")
            self.assertEqual(again.get("security_spike_mbps"), 5.0)

    def test_security_labels_exist_in_both_languages(self) -> None:
        for code in ("en", "ar"):
            set_language(code)
            for key in (
                "tab.security",
                "security.title",
                "security.kind.temp_path",
                "security.kind.mining_port",
                "security.kind.upload_spike",
                "security.severity.high",
                "security.scan_ips",
                "security.check_hash",
                "settings.group.security",
                "settings.security.abuse_key",
                "settings.hint.security",
            ):
                self.assertNotEqual(tr(key), key)
            self.assertNotEqual(
                tr("security.hint", total=2, ips=3),
                "security.hint",
            )


if __name__ == "__main__":
    unittest.main()
