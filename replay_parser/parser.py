from __future__ import annotations

import json
import os
import pathlib
from pathlib import Path
import subprocess
from threading import Thread
import sys
import traceback
import uuid
import requests
import re
from typing import List, Dict, Optional, Tuple, Union

from lib.data_classes.replay_data import ReplayData
from settings.settings import _settings


class PathNotExists(Exception):
    pass

class ReplayParserError(Exception):
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return str(Path(os.path.join(base_path, relative_path)))

_EXE = 'parser.exe' if os.name == 'nt' else 'parser'
_PATH = resource_path('replay_parser/bin/' + _EXE)
if not os.path.exists(_PATH):
    raise FileNotFoundError(f"The executable {_EXE} does not exist at {_PATH}")
_ARGUMENT = 'battle-results'

tanks_file_path = resource_path('tanks_names.json')
with open(tanks_file_path, "r", encoding = "utf-8-sig") as f:
    tank_names = json.load(f)

class ReplayParser:
    def __init__(self) -> None:
        self.res: ReplayData = None
        self.exc: Exception = None

    def parse(self, replay_path: str) -> ReplayData:
        """
        Parse a replay file and return the parsed data.
        
        Args:
            replay_path (str): The path to the replay file.
            auto_clear (bool, optional): Whether to automatically delete the replay file after parsing. Defaults to True.
            save_json (bool, optional): Whether to save the parsed data as a JSON file. Defaults to False.
        
        Returns:
            ReplayData: The parsed replay data.
        
        Raises:
            PathNotExists: If the specified replay file does not exist.
            ReplayParserError: If an error occurs while parsing the replay file.
        
        """
        def _parse_in_thread():
            self.res = None
            self.exc = None
            path = pathlib.PurePath(replay_path)
            if not pathlib.Path(replay_path).exists():
                # print(f'Path {replay_path} does not exist')
                raise PathNotExists(replay_path)
            
            # print(f'Executing replay parser: {_PATH}')

            replay_parser = subprocess.Popen([_PATH, _ARGUMENT, str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                stdout, stderr = replay_parser.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                # print(f'Failed to parse replay {replay_path}, TIMEOUT EXCEEDED')
                self.exc = ReplayParserError(f'Failed to parse replay {replay_path}, TIMEOUT EXCEEDED')
                return
            except Exception:
                # print(f'Failed to parse replay {replay_path}, unknown error')
                # print(traceback.format_exc())
                self.exc = ReplayParserError(f'Failed to parse replay {replay_path}, unknown error')
                return
            finally:
                replay_parser.terminate()

            if replay_parser.returncode != 0:
                self.exc = ReplayParserError(stderr.decode('utf-8'))
                return

            self.res = ReplayData.model_validate_json(stdout)

        thr = Thread(target=_parse_in_thread)
        thr.start()
        thr.join()

        if self.exc is not None:
            raise self.exc

        # print(self.res)
        return self.res



    def _bytes_from_hxd_text(self, txt: str) -> bytes:
        """
        Парсит текстовый дамп HxD -> bytes.
        Логика: для каждой строки, начинающейся с 8 шестнадцатеричных символов (offset),
        собираем все пары [0-9A-Fa-f]{2} после оффсета. ASCII-колонка игнорится.
        """
        out = bytearray()
        for line in txt.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("Offset("):
                continue
            # ожидаем строку вида "00000000  AA BB ...  <ASCII>"
            if len(s) < 8 or any(c not in "0123456789ABCDEF" for c in s[:8]):
                continue
            hex_part = s[8:]
            for m in re.finditer(r'\b([0-9A-Fa-f]{2})\b', hex_part):
                out.append(int(m.group(1), 16))
        return bytes(out)

    def _load_bytes(self, path: Union[str, Path]) -> bytes:
        p = Path(path)
        raw = p.read_bytes()
        # Если это HxD-текст (начинается с "Offset(h)"), пересобираем bytes:
        if raw.startswith("﻿Offset(h)".encode("utf-8", "ignore")) or raw.startswith(b"Offset(h)"):
            txt = raw.decode("utf-8", errors="replace")
            return self._bytes_from_hxd_text(txt)
        return raw

    def _read_varint(self, buf: bytes, idx: int) -> Tuple[Optional[int], int]:
        """Простой декодер protobuf-varint (unsigned). Возвращает (значение, следующий_индекс)."""
        shift = 0
        result = 0
        while idx < len(buf):
            b = buf[idx]
            idx += 1
            result |= (b & 0x7F) << shift
            if not (b & 0x80):
                return result, idx
            shift += 7
            if shift > 63:
                break
        return None, idx

    def extract_players(self, buf: bytes) -> List[Dict]:
        """
        Ищем блоки вида:  <ник>[A-Za-z0-9_]{2,32} 0x20 <01|02> 0x28 0x01 0x38 <varint account_id>
        За 17 байтов до начала каждого ника извлекаем Int16 значение
        """
        pat = re.compile(rb'(?P<nick>[A-Za-z0-9_]{2,32})\x20(?P<team>[\x01|\x02])\x28\x01\x38')
        players: List[Dict] = []

        for m in pat.finditer(buf):
            nick = m.group('nick').decode('ascii', errors='replace')
            team = 1 if m.group('team') == b'\x01' else 2

            # Извлекаем Int16 значение за 17 байтов до начала ника
            header_start = m.start() - 17
            if header_start >= 0 and header_start + 2 <= len(buf):
                int16_value = int.from_bytes(buf[header_start:header_start+2], byteorder='little', signed=False)
            else:
                int16_value = 0

            # varint сразу после 0x38
            account_id, after_varint_idx = self._read_varint(buf, m.end())

            # окно для поиска взвода/меток (подогнать длину при необходимости)
            win_start = after_varint_idx
            win_end = min(len(buf), after_varint_idx + 120)
            window = buf[win_start:win_end]

            # поиск тега клана.
            # Специфика: тег располагается через 11 байтов после конца ника и может быть 2..5 символов.
            clan_tag = None
            try:
                nick_end = m.start() + len(m.group('nick'))
                tag_offsets = [11, 12]

                for offset in tag_offsets:
                    tag_pos = nick_end + offset
                    if tag_pos >= len(buf):
                        continue

                    # Ищем 6–3 байт, чтобы захватывать служебную H в конец.
                    for L in range(6, 3 - 1, -1):
                        end = tag_pos + L
                        if end > len(buf):
                            continue

                        cand = buf[tag_pos:end]

                        # --- Удаляем служебную H в конце ---
                        if cand.endswith(b'H'):
                            cand = cand[:-1]  # просто отрезаем

                        # После обрезки длина должна быть от 2 до 5
                        if not (2 <= len(cand) <= 5):
                            continue

                        # Проверка валидности тега
                        if re.fullmatch(rb'[A-Za-z0-9_-]{2,5}', cand):
                            clan_tag = cand.decode('ascii', errors='replace')
                            break

                    if clan_tag:
                        break

                # fallback
                if clan_tag is None:
                    for rg in (
                        rb"\[([A-Za-z0-9_-]{2,5})\]",
                        rb"<([A-Za-z0-9_-]{2,5})>",
                        rb"\(([A-Za-z0-9_-]{2,5})\)"
                    ):
                        mtag = re.search(rg, window)
                        if mtag:
                            clan_tag = mtag.group(1).decode('ascii', errors='replace')
                            break

                    if clan_tag is None:
                        mtag = re.search(rb'\x20([A-Za-z0-9_-]{2,5})\x20', window)
                        if mtag:
                            clan_tag = mtag.group(1).decode('ascii', errors='replace')

            except Exception:
                clan_tag = None

            # поиск кандидата platoon_id: 6 байт, начинающиеся с 0x50 и оканчивающиеся 0x01
            platoon_id = None
            for i in range(0, max(0, len(window) - 5)):
                if window[i] == 0x50 and window[i+5] == 0x01:
                    platoon_id = window[i:i+6].hex().upper()
                    break

            players.append({
                "nick": nick,
                "team": team,
                "clan_tag": clan_tag,
                "account_id": account_id,
                "tank_id": int16_value,  # Int16 значение за 17 байтов до ника
                "tank_name": tank_names[str(int16_value)]["name"] if str(int16_value) in tank_names else "Unknown",
                "tank_level": tank_names[str(int16_value)]["level"] if str(int16_value) in tank_names else "0",
                "platoon_id": platoon_id  # hex string или None (6 байт вида 50......01)
            })
        # --- Присвоение номера взвода внутри команды ---
        # Для каждой команды формируем порядок встречающихся platoon_id и нумеруем их 1..N.
        team_platoon_map: Dict[int, Dict[str, int]] = {}
        for p in players:
            team = p.get("team")
            plat = p.get("platoon_id")
            if team not in team_platoon_map:
                team_platoon_map[team] = {}
            if plat and plat not in team_platoon_map[team]:
                # назначаем следующий номер для нового platoon_id в команде
                team_platoon_map[team][plat] = len(team_platoon_map[team]) + 1

        # заполняем поле platoon_index (0 = нет взвода)
        for p in players:
            plat = p.get("platoon_id")
            if plat:
                p["platoon_index"] = team_platoon_map[p.get("team")].get(plat, 0)
            else:
                p["platoon_index"] = 0

        return players


    def parse_data_replay(self, replay_path: Union[str, Path]) -> dict:
        """
        Парсит реплей, возвращает словарь с данными.
        """
        buf = self._load_bytes(replay_path)
        players = self.extract_players(buf)

        if players is None or len(players) < 1:
            raise ReplayParserError("No players found in replay")

        plrs1 = []
        plrs2 = []
        for p in players:
            plrs1.append(p["account_id"]) if p["team"] == 1 else plrs2.append(p["account_id"])
            # print(f"{p['team']}: {p['nick']}, {p['account_id']}")
        plrs = plrs1 + plrs2

        _json = {"license_key":"key-RnSKdMNm10Fh86cb8lg21hunTR8y7Cy1","device_id":"00e097235a2e","players":plrs}
        response = requests.post(url = "http://212.80.7.214:20060/parse_players", json = _json)
        data = response.json()
        # print(data)

        folder_name = str(pathlib.Path(replay_path).parent.name)
        if folder_name.startswith("recording_"):
            folder_name = folder_name[len("recording_"):]
        if folder_name.endswith(".tbreplay"):
            folder_name = folder_name[:-len(".tbreplay")]
        if folder_name.endswith(".wotbreplay"):
            folder_name = folder_name[:-len(".wotbreplay")]

        team_1 = []
        team_2 = []
        author_nickname = folder_name

        # initialize author_team; if author nickname not found, we'll raise an error
        author_team = None

        for p in players:
            if p["nick"] == author_nickname:
                author_team = p["team"]
            pdata = data['players_data'][str(p["account_id"])]
            pdata["nickname"] = p["nick"]
            # добавляем информацию о теге клана, если была найдена
            pdata["clan_tag"] = p.get("clan_tag")
            pdata["tank_id"] = p["tank_id"]
            pdata["tank_name"] = p["tank_name"]
            pdata["tank_level"] = p["tank_level"]
            pdata["platoon_index"] = p["platoon_index"]
            team_1.append(pdata) if p["team"] == 1 else team_2.append(pdata)

        if author_team is None:
            # couldn't find author in parsed players — replay folder name may not match any nick
            raise ReplayParserError(f"Author nickname '{author_nickname}' not found in replay players")

        if author_team == 1:
            return {"team_1": team_1, "team_2": team_2, "author_team": author_team, "author_nickname": author_nickname}
        return {"team_1": team_2, "team_2": team_1, "author_team": author_team, "author_nickname": author_nickname}
