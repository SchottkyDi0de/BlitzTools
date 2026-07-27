from __future__ import annotations

import platform
import re
from pathlib import Path

from utils.admin import is_elevated

MARKER_BEGIN = "# >>> BlitzTools clusters"
MARKER_END = "# <<< BlitzTools clusters"
BLOCK_IP = "127.0.0.1"


class HostsBlockerError(Exception):
    pass


class HostsBlocker:
    def __init__(self, hosts_path: Path | None = None):
        self.hosts_path = hosts_path or self._default_hosts_path()

    @staticmethod
    def _default_hosts_path() -> Path:
        if platform.system() == "Windows":
            return Path(r"C:\Windows\System32\drivers\etc\hosts")
        return Path("/etc/hosts")

    def read_blocked(self) -> set[str]:
        if not self.hosts_path.exists():
            return set()

        text = self.hosts_path.read_text(encoding="utf-8", errors="replace")
        section = self._extract_section(text)
        if not section:
            return set()

        blocked: set[str] = set()
        for line in section.splitlines():
            hostname = self._parse_blocked_line(line)
            if hostname:
                blocked.add(hostname)
        return blocked

    def set_blocked(self, hostnames: set[str]) -> None:
        if not is_elevated():
            raise HostsBlockerError("admin_required")

        normalized = {name.strip().lower() for name in hostnames if name.strip()}
        text = ""
        if self.hosts_path.exists():
            text = self.hosts_path.read_text(encoding="utf-8", errors="replace")

        without_section = self._remove_section(text).rstrip()
        if not normalized:
            self._write_text(without_section + ("\n" if without_section else ""))
            return

        lines = [MARKER_BEGIN]
        for hostname in sorted(normalized):
            lines.append(f"{BLOCK_IP} {hostname}")
        lines.append(MARKER_END)

        block = "\n".join(lines)
        if without_section:
            new_text = without_section + "\n\n" + block + "\n"
        else:
            new_text = block + "\n"
        self._write_text(new_text)

    def block(self, hostnames: set[str]) -> None:
        current = self.read_blocked()
        current.update(name.strip().lower() for name in hostnames if name.strip())
        self.set_blocked(current)

    def unblock(self, hostnames: set[str]) -> None:
        current = self.read_blocked()
        for name in hostnames:
            current.discard(name.strip().lower())
        self.set_blocked(current)

    def unblock_all(self) -> None:
        self.set_blocked(set())

    def _write_text(self, text: str) -> None:
        try:
            self.hosts_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise HostsBlockerError("write_failed") from exc

    @staticmethod
    def _extract_section(text: str) -> str | None:
        pattern = re.compile(
            rf"^{re.escape(MARKER_BEGIN)}\s*$([\s\S]*?)^\s*{re.escape(MARKER_END)}\s*$",
            re.MULTILINE,
        )
        match = pattern.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _remove_section(text: str) -> str:
        pattern = re.compile(
            rf"^\s*{re.escape(MARKER_BEGIN)}\s*$[\s\S]*?^\s*{re.escape(MARKER_END)}\s*$\n?",
            re.MULTILINE,
        )
        return pattern.sub("", text)

    @staticmethod
    def _parse_blocked_line(line: str) -> str | None:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None
        parts = stripped.split()
        if len(parts) < 2:
            return None
        if parts[0] != BLOCK_IP:
            return None
        return parts[1].lower()
