from __future__ import annotations

import pathlib
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from lib.replay_parser.errors import ReplayParserError
from lib.replay_parser.marks import decode_marks_value, extract_marks, player_info_marks
from lib.replay_parser.models.battle_results_dat import BattleResultsDat
from lib.replay_parser.models.region import Region

_UINT64_MAX = 18446744073709551615
_MAX_RAW_TEAM = 15
_PLAYER_PATTERN = re.compile(
    rb"(?P<nick>[A-Za-z0-9_]{2,32})\x20(?P<team>[\x01-\x0f])\x28\x01\x38"
)


class LivePlayer(BaseModel):
    """Игрок, извлечённый из data.replay / data.wotreplay без battle_results.dat."""

    model_config = ConfigDict(frozen=False)

    nickname: str
    team: int = Field(ge=1, le=_MAX_RAW_TEAM, description="Номер команды в реплее (1–2 в обычном бою)")
    account_id: int | None = None
    clan_tag: str | None = None
    tank_id: int = 0
    marks: int = Field(default=0, ge=0, le=3)
    platoon_id: int | None = None
    platoon_index: int = Field(default=0, ge=0)
    avatar_url: str = ""
    frame_kind: str = ""
    profile_skin_url: str = ""

    _proto_start: int | None = PrivateAttr(default=None)

    @property
    def in_platoon(self) -> bool:
        return self.platoon_index > 0


class LiveReplay(BaseModel):
    """Roster боя из live-файла реплея; team_1 — команда автора (если он в ростере)."""

    model_config = ConfigDict(frozen=False)

    author_nickname: str
    author_team: int = Field(ge=1, le=2)
    author_in_roster: bool = True
    region: Region
    team_1: list[LivePlayer] = Field(default_factory=list)
    team_2: list[LivePlayer] = Field(default_factory=list)

    @property
    def all_players(self) -> list[LivePlayer]:
        return self.team_1 + self.team_2

    @property
    def author(self) -> LivePlayer:
        if not self.author_in_roster:
            raise ReplayParserError(
                f"Author nickname '{self.author_nickname}' is not in replay players "
                "(temporary mode or non-standard battle)"
            )
        for player in self.all_players:
            if player.nickname == self.author_nickname:
                return player
        raise ReplayParserError(f"Author nickname '{self.author_nickname}' not found in replay players")

    def player_by_nickname(self, nickname: str) -> LivePlayer:
        for player in self.all_players:
            if player.nickname == nickname:
                return player
        raise KeyError(nickname)


class LiveReplayExtractor:
    """Извлекает игроков и автора из бинарного data.replay / data.wotreplay."""

    @staticmethod
    def author_nickname_from_path(replay_path: str | Path) -> str:
        folder_name = pathlib.Path(replay_path).parent.name
        if folder_name.startswith("recording_"):
            folder_name = folder_name[len("recording_") :]
        if folder_name.endswith(".tbreplay"):
            folder_name = folder_name[: -len(".tbreplay")]
        if folder_name.endswith(".wotbreplay"):
            folder_name = folder_name[: -len(".wotbreplay")]
        return folder_name

    def extract(self, replay_path: str | Path) -> LiveReplay:
        path = Path(replay_path)
        if not path.exists():
            raise FileNotFoundError(replay_path)

        buf = self._load_bytes(path)
        region = self._region_from_replay_path(path)
        marks_by_account = self._marks_by_account_from_battle_results(path)
        players = self._extract_players(buf)
        self._apply_marks(players, buf, marks_by_account, region)
        if not players:
            raise ReplayParserError("No players found in replay")

        author_nickname = self.author_nickname_from_path(path)
        team_1, team_2, author_team, author_in_roster = self._split_teams(players, author_nickname)

        return LiveReplay(
            author_nickname=author_nickname,
            author_team=author_team,
            author_in_roster=author_in_roster,
            region=region,
            team_1=team_1,
            team_2=team_2,
        )

    @staticmethod
    def _is_free_for_all(players: list[LivePlayer]) -> bool:
        return len({player.team for player in players}) > 2

    @classmethod
    def _split_teams(
        cls,
        players: list[LivePlayer],
        author_nickname: str,
    ) -> tuple[list[LivePlayer], list[LivePlayer], int, bool]:
        author_player = next(
            (player for player in players if player.nickname == author_nickname),
            None,
        )

        if author_player is None:
            if cls._is_free_for_all(players):
                for player in players:
                    player.team = 2
                    player.platoon_id = None
                    player.platoon_index = 0
                return [], players, 1, False

            team_1 = [player for player in players if player.team == 1]
            team_2 = [player for player in players if player.team == 2]
            return team_1, team_2, 1, False

        if cls._is_free_for_all(players):
            team_1 = [author_player]
            team_2 = [player for player in players if player.nickname != author_nickname]
            author_player.team = 1
            for player in team_2:
                player.team = 2
                player.platoon_id = None
                player.platoon_index = 0
            return team_1, team_2, 1, True

        author_team = author_player.team
        team_1_raw = [player for player in players if player.team == 1]
        team_2_raw = [player for player in players if player.team == 2]
        if author_team == 1:
            return team_1_raw, team_2_raw, author_team, True
        return team_2_raw, team_1_raw, author_team, True

    def _bytes_from_hxd_text(self, txt: str) -> bytes:
        out = bytearray()
        for line in txt.splitlines():
            s = line.strip()
            if not s or s.startswith("Offset("):
                continue
            if len(s) < 8 or any(c not in "0123456789ABCDEF" for c in s[:8]):
                continue
            hex_part = s[8:]
            for match in re.finditer(r"\b([0-9A-Fa-f]{2})\b", hex_part):
                out.append(int(match.group(1), 16))
        return bytes(out)

    def _load_bytes(self, path: str | Path) -> bytes:
        raw = Path(path).read_bytes()
        if raw.startswith("﻿Offset(h)".encode("utf-8", "ignore")) or raw.startswith(b"Offset(h)"):
            txt = raw.decode("utf-8", errors="replace")
            return self._bytes_from_hxd_text(txt)
        return raw

    def _read_varint(self, buf: bytes, idx: int) -> tuple[Optional[int], int]:
        shift = 0
        result = 0
        while idx < len(buf):
            byte = buf[idx]
            idx += 1
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                return result, idx
            shift += 7
            if shift > 63:
                break
        return None, idx

    def _parse_proto_fields(self, buf: bytes) -> dict[int, list]:
        fields: dict[int, list] = {}
        pos = 0
        while pos < len(buf):
            tag, pos = self._read_varint(buf, pos)
            if tag is None:
                break
            field_number = tag >> 3
            wire_type = tag & 7
            if wire_type == 0:
                value, pos = self._read_varint(buf, pos)
                if value is not None:
                    fields.setdefault(field_number, []).append(value)
            elif wire_type == 2:
                length, pos = self._read_varint(buf, pos)
                if length is None or pos + length > len(buf):
                    break
                fields.setdefault(field_number, []).append(buf[pos : pos + length])
                pos += length
            elif wire_type == 5:
                pos += 4
            elif wire_type == 1:
                pos += 8
            else:
                break
        return fields

    def _marks_from_ru_fields(self, fields: dict[int, list]) -> int:
        for submessage in fields.get(25, []):
            if not isinstance(submessage, bytes):
                continue
            nested = self._parse_proto_fields(submessage)
            for value in nested.get(1, []):
                if isinstance(value, int):
                    return decode_marks_value(value)
        return 0

    def _marks_from_eu_fields(self, fields: dict[int, list]) -> int:
        field_22 = next((value for value in fields.get(22, []) if isinstance(value, int)), None)
        if field_22 == _UINT64_MAX:
            for value in fields.get(26, []):
                if isinstance(value, int):
                    marks = decode_marks_value(value)
                    if marks:
                        return marks

        for value in fields.get(124, []):
            if isinstance(value, int):
                marks = decode_marks_value(value)
                if marks:
                    return marks
        return 0

    @staticmethod
    def _platoon_id_from_fields(fields: dict[int, list]) -> int | None:
        for value in fields.get(10, []):
            if isinstance(value, int) and value > 0:
                return value
        return None

    @staticmethod
    def _first_proto_string(fields: dict[int, list], field_number: int) -> str:
        for value in fields.get(field_number, []):
            if isinstance(value, bytes):
                try:
                    return value.decode("utf-8")
                except UnicodeDecodeError:
                    continue
        return ""

    @staticmethod
    def _pick_media_url(gfx_url: str, gfx2_url: str) -> str:
        for url in (gfx2_url, gfx_url):
            if url and not url.lower().endswith(".webp"):
                return url
        return gfx_url or gfx2_url or ""

    def _avatar_from_fields(self, fields: dict[int, list]) -> tuple[str, str]:
        for submessage in fields.get(17, []):
            if not isinstance(submessage, bytes):
                continue
            inner = self._parse_proto_fields(submessage)
            avatar_blob = next((value for value in inner.get(2, []) if isinstance(value, bytes)), None)
            if avatar_blob is None:
                avatar_blob = submessage
            info = self._parse_proto_fields(avatar_blob)
            gfx_url = self._first_proto_string(info, 2)
            gfx2_url = self._first_proto_string(info, 3)
            kind = self._first_proto_string(info, 4)
            if gfx_url or gfx2_url or kind:
                return self._pick_media_url(gfx_url, gfx2_url), kind
        return "", ""

    @staticmethod
    def _looks_like_profile_skin_url(url: str) -> bool:
        if not url or not url.isprintable():
            return False
        lower = url.lower()
        if lower.startswith("http://") or lower.startswith("https://"):
            return True
        return "profile_skin" in lower or "anim_profile" in lower

    def _profile_skin_from_submessage(self, inner: dict[int, list]) -> str:
        gfx2_url = self._first_proto_string(inner, 2)
        gfx_url = self._first_proto_string(inner, 3)
        url = self._pick_media_url(gfx_url, gfx2_url)
        if self._looks_like_profile_skin_url(url):
            return url
        return ""

    def _profile_skin_from_fields(self, fields: dict[int, list]) -> str:
        for field_number in (23, 24):
            for submessage in fields.get(field_number, []):
                if not isinstance(submessage, bytes):
                    continue
                inner = self._parse_proto_fields(submessage)
                url = self._profile_skin_from_submessage(inner)
                if url:
                    return url
        return ""

    @staticmethod
    def _assign_platoon_indexes(players: list[LivePlayer]) -> None:
        members: dict[tuple[int, int], list[LivePlayer]] = {}
        for player in players:
            if player.platoon_id is None:
                player.platoon_index = 0
                continue
            key = (player.team, int(player.platoon_id))
            members.setdefault(key, []).append(player)

        platoons_by_team: dict[int, list[tuple[int, list[LivePlayer]]]] = {}
        for (team, platoon_id), group in members.items():
            if len(group) < 2:
                for member in group:
                    member.platoon_id = None
                    member.platoon_index = 0
                continue
            platoons_by_team.setdefault(team, []).append((platoon_id, group))

        for platoons in platoons_by_team.values():
            for index, (_, group) in enumerate(sorted(platoons, key=lambda item: item[0]), start=1):
                for member in group:
                    member.platoon_index = index

    def _marks_from_proto_chunk(self, buf: bytes, start: int, region: Region, size: int = 800) -> int:
        fields = self._parse_proto_fields(buf[start : start + size])
        if region == Region.RU:
            return self._marks_from_ru_fields(fields)
        return self._marks_from_eu_fields(fields)

    @staticmethod
    def _region_from_replay_path(replay_path: str | Path) -> Region:
        parent = Path(replay_path).parent
        if parent.suffix == ".tbreplay" or parent.name.endswith(".tbreplay"):
            return Region.RU
        if parent.suffix == ".wotbreplay" or parent.name.endswith(".wotbreplay"):
            return Region.EU
        return Region.RU

    def _marks_by_account_from_battle_results(self, replay_path: str | Path) -> dict[int, int]:
        battle_results_path = Path(replay_path).parent / "battle_results.dat"
        if not battle_results_path.exists():
            return {}

        region = self._region_from_replay_path(replay_path)
        with battle_results_path.open("rb") as handle:
            battle_results = BattleResultsDat.from_reader(handle).decode(region)

        results_by_account = {
            result.info.account_id: result.info for result in battle_results.player_results
        }
        marks_by_account: dict[int, int] = {}
        for player in battle_results.players:
            account_id = int(player.account_id)
            result_info = results_by_account.get(player.account_id)
            if result_info is None:
                marks_by_account[account_id] = player_info_marks(player.info)
                continue
            marks_by_account[account_id] = max(
                extract_marks(region, result_info),
                player_info_marks(player.info),
            )
        return marks_by_account

    def _apply_marks(
        self,
        players: list[LivePlayer],
        buf: bytes,
        marks_by_account: dict[int, int],
        region: Region,
    ) -> None:
        for player in players:
            if player.account_id is None:
                player.marks = 0
                continue

            marks_from_data = 0
            if player._proto_start is not None:
                marks_from_data = self._marks_from_proto_chunk(buf, player._proto_start, region)

            player.marks = max(
                marks_from_data,
                marks_by_account.get(int(player.account_id), 0),
            )
            player._proto_start = None

    def _extract_players(self, buf: bytes) -> list[LivePlayer]:
        players: list[LivePlayer] = []
        seen_accounts: set[int] = set()

        for match in _PLAYER_PATTERN.finditer(buf):
            nickname = match.group("nick").decode("ascii", errors="replace")
            team = match.group("team")[0]

            header_start = match.start() - 17
            if header_start >= 0 and header_start + 2 <= len(buf):
                tank_id = int.from_bytes(
                    buf[header_start : header_start + 2],
                    byteorder="little",
                    signed=False,
                )
            else:
                tank_id = 0

            account_id, after_varint_idx = self._read_varint(buf, match.end())
            if account_id is not None and account_id in seen_accounts:
                continue
            if account_id is not None:
                seen_accounts.add(account_id)

            win_start = after_varint_idx
            win_end = min(len(buf), after_varint_idx + 120)
            window = buf[win_start:win_end]

            clan_tag = self._extract_clan_tag(buf, match, window)

            proto_fields = self._parse_proto_fields(buf[after_varint_idx : after_varint_idx + 800])
            platoon_id = self._platoon_id_from_fields(proto_fields)
            avatar_url, frame_kind = self._avatar_from_fields(proto_fields)
            profile_skin_url = self._profile_skin_from_fields(proto_fields)

            player = LivePlayer(
                nickname=nickname,
                team=team,
                clan_tag=clan_tag,
                account_id=account_id,
                tank_id=tank_id,
                platoon_id=platoon_id,
                avatar_url=avatar_url,
                frame_kind=frame_kind,
                profile_skin_url=profile_skin_url,
            )
            player._proto_start = after_varint_idx
            players.append(player)

        self._assign_platoon_indexes(players)
        return players

    @staticmethod
    def _extract_clan_tag(buf: bytes, match: re.Match[bytes], window: bytes) -> str | None:
        try:
            nick_end = match.start() + len(match.group("nick"))
            for offset in (11, 12):
                tag_pos = nick_end + offset
                if tag_pos >= len(buf):
                    continue
                for length in range(6, 3, -1):
                    end = tag_pos + length
                    if end > len(buf):
                        continue
                    candidate = buf[tag_pos:end]
                    if candidate.endswith(b"H"):
                        candidate = candidate[:-1]
                    if not (2 <= len(candidate) <= 5):
                        continue
                    if re.fullmatch(rb"[A-Za-z0-9_-]{2,5}", candidate):
                        return candidate.decode("ascii", errors="replace")
            for pattern in (
                rb"\[([A-Za-z0-9_-]{2,5})\]",
                rb"<([A-Za-z0-9_-]{2,5})>",
                rb"\(([A-Za-z0-9_-]{2,5})\)",
            ):
                tag_match = re.search(pattern, window)
                if tag_match:
                    return tag_match.group(1).decode("ascii", errors="replace")
            tag_match = re.search(rb"\x20([A-Za-z0-9_-]{2,5})\x20", window)
            if tag_match:
                return tag_match.group(1).decode("ascii", errors="replace")
        except Exception:
            return None
        return None


def parse_live_replay(replay_path: str | Path) -> LiveReplay:
    """Парсит data.replay / data.wotreplay и возвращает LiveReplay."""
    return LiveReplayExtractor().extract(replay_path)
