from __future__ import annotations

"""Native NETLINK_SOCK_DIAG collector.

pyroute2 is used instead of parsing ``ss`` output.  It is a mature Netlink
library with a permissive dual license (GPL-2.0-or-later OR Apache-2.0), which
is compatible with this project's GPL-3.0-or-later license.

TCP sockets expose cumulative ``tcpi_bytes_sent`` / ``tcpi_bytes_received``.
UDP has no equivalent kernel counter through sock_diag, so UDP sockets are
reported with ``measured=False`` instead of a misleading zero speed.
"""

import socket
from typing import Any

from .net_conn import (
    SocketRecord,
    format_netlink_address,
    format_netlink_port,
)


class NetlinkBackend:
    def __init__(self) -> None:
        self.last_error: str | None = None
        self._import_error: str | None = None

    @property
    def available(self) -> bool:
        return self._import_error is None and self._can_import()

    @staticmethod
    def _can_import() -> bool:
        try:
            from pyroute2.netlink.diag import DiagSocket  # noqa: F401
        except Exception:
            return False
        return True

    def check(self) -> str | None:
        """Return an error string when pyroute2 is unavailable, else None."""
        try:
            from pyroute2.netlink.diag import DiagSocket  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            self._import_error = str(exc) or "pyroute2 is not installed"
            return self._import_error
        self._import_error = None
        return None

    @staticmethod
    def _attrs(message: Any) -> dict[str, Any]:
        raw = message.get("attrs") or []
        if isinstance(raw, dict):
            return dict(raw)
        result: dict[str, Any] = {}
        try:
            for item in raw:
                if isinstance(item, dict):
                    result.update({str(key): value for key, value in item.items()})
                    continue
                name = getattr(item, "name", None)
                if name is not None:
                    result[str(name)] = getattr(item, "value", None)
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    result[str(item[0])] = item[1]
        except TypeError:
            pass
        return result

    @staticmethod
    def _tcp_counters(info: Any) -> tuple[int, int, bool]:
        if not isinstance(info, dict):
            try:
                info = dict(info)
            except (TypeError, ValueError):
                return 0, 0, False
        rx = info.get("tcpi_bytes_received")
        tx = info.get("tcpi_bytes_sent")
        if tx is None:
            tx = info.get("tcpi_bytes_acked")
        if rx is None and tx is None:
            return 0, 0, False
        try:
            return max(0, int(tx or 0)), max(0, int(rx or 0)), True
        except (TypeError, ValueError):
            return 0, 0, False

    def poll(self) -> tuple[list[SocketRecord], str | None]:
        error = self.check()
        if error:
            self.last_error = error
            return [], error

        from pyroute2.netlink.diag import (  # type: ignore[import-not-found]
            AF_INET,
            AF_INET6,
            IPPROTO_TCP,
            SS_ALL,
            DiagSocket,
        )

        records: list[SocketRecord] = []
        errors: list[str] = []
        for family in (AF_INET, AF_INET6):
            try:
                with DiagSocket() as diag:
                    tcp_messages = diag.get_sock_stats(
                        family=family,
                        states=SS_ALL,
                        protocol=IPPROTO_TCP,
                        extensions=2,  # INET_DIAG_INFO (tcp_info)
                    )
                    for message in tcp_messages:
                        state = int(message.get("idiag_state", 0) or 0)
                        if state == 10:  # LISTEN
                            continue
                        inode = int(message.get("idiag_inode", 0) or 0)
                        if inode <= 0:
                            continue
                        attrs = self._attrs(message)
                        tx, rx, measured = self._tcp_counters(attrs.get("INET_DIAG_INFO"))
                        uid_value = message.get("idiag_uid", -1)
                        records.append(
                            SocketRecord(
                                inode=inode,
                                protocol="tcp",
                                state=state,
                                uid=int(uid_value) if uid_value is not None else -1,
                                tx=tx,
                                rx=rx,
                                measured=measured,
                                local_addr=format_netlink_address(
                                    message.get("idiag_src"), family
                                ),
                                local_port=format_netlink_port(message.get("idiag_sport")),
                                remote_addr=format_netlink_address(
                                    message.get("idiag_dst"), family
                                ),
                                remote_port=format_netlink_port(message.get("idiag_dport")),
                            )
                        )

                    udp_messages = diag.get_sock_stats(
                        family=family,
                        states=SS_ALL,
                        protocol=socket.IPPROTO_UDP,
                        extensions=0,
                    )
                    for message in udp_messages:
                        inode = int(message.get("idiag_inode", 0) or 0)
                        if inode <= 0:
                            continue
                        uid_value = message.get("idiag_uid", -1)
                        records.append(
                            SocketRecord(
                                inode=inode,
                                protocol="udp",
                                state=int(message.get("idiag_state", 0) or 0),
                                uid=int(uid_value) if uid_value is not None else -1,
                                tx=0,
                                rx=0,
                                measured=False,
                                local_addr=format_netlink_address(
                                    message.get("idiag_src"), family
                                ),
                                local_port=format_netlink_port(message.get("idiag_sport")),
                                remote_addr=format_netlink_address(
                                    message.get("idiag_dst"), family
                                ),
                                remote_port=format_netlink_port(message.get("idiag_dport")),
                            )
                        )
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc) or exc.__class__.__name__)

        # Deduplicate inodes (IPv4/IPv6 dumps can overlap in unusual setups).
        unique: dict[int, SocketRecord] = {}
        for record in records:
            unique.setdefault(record.inode, record)
        if errors and not unique:
            self.last_error = "; ".join(errors)
            return [], self.last_error
        self.last_error = "; ".join(errors) if errors else None
        return list(unique.values()), self.last_error
