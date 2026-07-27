from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.replay_parser.live_replay import LivePlayer, LiveReplay, LiveReplayExtractor

try:
    from kivy import Logger as _log
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger("tests.replay")

DATA_REPLAY_PATH = Path(
    r"C:\Users\cookie\Documents\TanksBlitz\replays\recording_nyTeLLlecTBeHHuK.tbreplay\data.replay"
)
EU_DATA_REPLAY_PATH = Path(
    r"C:\Users\cookie\Documents\TanksBlitz\replays\recording__Semen_Van_.wotbreplay\data.wotreplay"
)
KORBEN_DATA_REPLAY_PATH = Path(
    r"C:\Users\cookie\Documents\TanksBlitz\replays\recording_KorbenDallas_TopSosok.tbreplay\data.replay"
)


def _assert_platoon_groups(team: list[LivePlayer], expected_groups: list[frozenset[int]]) -> None:
    """Проверяет, что игроки сгруппированы в взводы по account_id."""
    for group_accounts in expected_groups:
        members = [player for player in team if player.account_id in group_accounts]
        assert len(members) == len(group_accounts), (
            f"expected platoon members {group_accounts}, found {[p.account_id for p in members]}"
        )
        platoon_ids = {player.platoon_id for player in members}
        indexes = {player.platoon_index for player in members}
        assert len(platoon_ids) == 1 and None not in platoon_ids, f"platoon_id mismatch in {group_accounts}"
        assert len(indexes) == 1 and 0 not in indexes, f"platoon_index mismatch in {group_accounts}"

    platoon_member_ids = {account_id for group in expected_groups for account_id in group}
    for player in team:
        if player.account_id in platoon_member_ids:
            continue
        assert player.platoon_id is None and player.platoon_index == 0, (
            f"{player.nickname} should not be in a platoon"
        )


class ReplayExtractionTest:
    """Тест извлечения автора и игроков из data.replay (RU)."""

    def __init__(self, replay_path: Path = DATA_REPLAY_PATH) -> None:
        self.replay_path = replay_path
        self.extractor = LiveReplayExtractor()

    def run(self) -> None:
        _log.info(f"Tests RU: extracting players from {self.replay_path}...")
        assert self.replay_path.exists(), f"data.replay not found: {self.replay_path}"

        result = self.extractor.extract(self.replay_path)
        players = result.all_players
        total = len(players)

        assert result.author_nickname == "nyTeLLlecTBeHHuK", f"unexpected author: {result.author_nickname}"
        assert 10 <= total <= 30, f"unexpected player count: {total}"
        assert any(player.nickname == result.author_nickname for player in players), "author not in player list"
        assert all(player.account_id is not None for player in players), "missing account_id"
        assert all(player.team in (1, 2) for player in players), "invalid team number"
        assert all(0 <= player.marks <= 3 for player in players), "invalid marks"
        assert all(player.avatar_url is not None and player.frame_kind is not None for player in players)

        expected_marks = {
            "nyTeLLlecTBeHHuK": 3,
            "6eLLIeHa9I_Ta6ypeTka": 1,
            "prepare": 3,
            "TheDarkTriad": 3,
            "_C_BuPeTTblu_BoJlk_": 1,
        }
        for player in players:
            expected = expected_marks.get(player.nickname, 0)
            assert player.marks == expected, (
                f"{player.nickname}: expected {expected} marks, got {player.marks}"
            )

        marked = [player for player in players if player.marks > 0]
        assert len(marked) == len(expected_marks), (
            f"unexpected marked players: {[(p.nickname, p.marks) for p in marked]}"
        )

        author_player = result.author
        assert author_player.frame_kind == "legendary", author_player.frame_kind
        assert "avatar_may24_legendary_anim" in author_player.avatar_url, author_player.avatar_url
        assert "profile_skin_bp_32" in author_player.profile_skin_url, author_player.profile_skin_url

        prepare = result.player_by_nickname("prepare")
        assert prepare.frame_kind == "rare"
        assert "avatar_smiley_deer_rare" in prepare.avatar_url
        assert not prepare.profile_skin_url

        ru_platoon_allies = {
            result.player_by_nickname("hidikh1982").platoon_id,
            result.player_by_nickname("ABBADON_12").platoon_id,
        }
        ru_platoon_enemies = {
            result.player_by_nickname("prepare").platoon_id,
            result.player_by_nickname("TheDarkTriad").platoon_id,
        }
        assert len(ru_platoon_allies) == 1 and None not in ru_platoon_allies, "allies platoon id mismatch"
        assert len(ru_platoon_enemies) == 1 and None not in ru_platoon_enemies, "enemies platoon id mismatch"
        assert ru_platoon_allies != ru_platoon_enemies, "allies and enemies must be different platoons"

        for nick in ("hidikh1982", "ABBADON_12", "prepare", "TheDarkTriad"):
            player = result.player_by_nickname(nick)
            assert player.platoon_index == 1, f"{nick}: expected platoon_index 1, got {player.platoon_index}"

        for nick in ("nyTeLLlecTBeHHuK", "P696508", "naDGoB_stand"):
            player = result.player_by_nickname(nick)
            assert player.platoon_id is None and player.platoon_index == 0, f"{nick} should not be in platoon"

        _log.info(f"Tests RU: replay extraction passed! author={result.author_nickname}, players={total}")
        _log.info(
            "  marks: "
            + ", ".join(f"{p.nickname}={p.marks}" for p in sorted(players, key=lambda x: x.marks, reverse=True))
        )
        _log.info(
            "  platoons: "
            + ", ".join(
                f"{p.nickname}(id={p.platoon_id}, idx={p.platoon_index})"
                for p in players
                if p.platoon_index
            )
        )
        _log.info(
            "  avatars: "
            + ", ".join(
                f"{p.nickname}(kind={p.frame_kind}, skin={'yes' if p.profile_skin_url else 'no'})"
                for p in players
                if p.frame_kind or p.profile_skin_url
            )
        )


class ReplayKorbenPlatoonTest:
    """Тест взводов на data.replay (RU, два взвода на команду)."""

    def __init__(self, replay_path: Path = KORBEN_DATA_REPLAY_PATH) -> None:
        self.replay_path = replay_path
        self.extractor = LiveReplayExtractor()

    def run(self) -> None:
        _log.info(f"Tests RU Korben: extracting players from {self.replay_path}...")
        assert self.replay_path.exists(), f"data.replay not found: {self.replay_path}"

        result: LiveReplay = self.extractor.extract(self.replay_path)
        players = result.all_players

        assert result.author_nickname == "KorbenDallas_TopSosok", f"unexpected author: {result.author_nickname}"
        assert len(players) == 14, f"unexpected player count: {len(players)}"

        _assert_platoon_groups(
            result.team_1,
            [
                frozenset({150804716, 214013550}),
                frozenset({71554775, 28777456, 111143230}),
            ],
        )
        _assert_platoon_groups(
            result.team_2,
            [
                frozenset({170501762, 115186115}),
                frozenset({172373167, 303225457, 35639973}),
            ],
        )

        platoon_indexes = sorted({player.platoon_index for player in players if player.platoon_index})
        assert platoon_indexes == [1, 2], f"expected platoon indexes 1 and 2 per team, got {platoon_indexes}"

        for nick, expected_idx, expected_id in (
            ("KorbenDallas_TopSosok", 1, 14832938),
            ("4auHuK_u3_TTpuTT9ITu", 1, 14832938),
            ("_SKILETON_2017_", 2, 16282556),
            ("Zorigto1988", 2, 16282556),
            ("G0r3c_Na_GuseNICax_013", 2, 16282556),
            ("LightningTank", 1, 17007343),
            ("Joker___top", 1, 17007343),
            ("OXOTA__H_A_4_A_Jl_A_C_b", 2, 17452649),
            ("Sheptun56", 2, 17452649),
            ("CTAR6IY_DULOVOD", 2, 17452649),
        ):
            player = result.player_by_nickname(nick)
            assert player.platoon_id == expected_id, f"{nick}: platoon_id"
            assert player.platoon_index == expected_idx, f"{nick}: platoon_index"

        korben = result.player_by_nickname("KorbenDallas_TopSosok")
        assert korben.frame_kind == "unique"
        assert "anim_profile_skin_2025_BLACK" in korben.profile_skin_url

        lightning = result.player_by_nickname("LightningTank")
        assert lightning.frame_kind == "rare"
        assert "profile_skin_deepwat_l" in lightning.profile_skin_url

        _log.info(f"Tests RU Korben: passed! author={result.author_nickname}")
        _log.info(
            "  platoons: "
            + ", ".join(
                f"{p.nickname}(id={p.platoon_id}, idx={p.platoon_index})"
                for p in players
                if p.platoon_index
            )
        )


class ReplayEuExtractionTest:
    """Тест извлечения автора и игроков из data.wotreplay (EU)."""

    def __init__(self, replay_path: Path = EU_DATA_REPLAY_PATH) -> None:
        self.replay_path = replay_path
        self.extractor = LiveReplayExtractor()

    def run(self) -> None:
        _log.info(f"Tests EU: extracting players from {self.replay_path}...")
        assert self.replay_path.exists(), f"data.wotreplay not found: {self.replay_path}"

        result = self.extractor.extract(self.replay_path)
        players = result.all_players

        assert result.author_nickname == "_Semen_Van_", f"unexpected author: {result.author_nickname}"
        assert len(players) == 14, f"unexpected player count: {len(players)}"

        for player in players:
            expected = 1 if player.nickname == result.author_nickname else 0
            assert player.marks == expected, (
                f"{player.nickname}: expected {expected} marks, got {player.marks}"
            )

        marked = [player for player in players if player.marks > 0]
        assert len(marked) == 1 and marked[0].nickname == result.author_nickname, (
            f"expected marks only for author, got: {[(p.nickname, p.marks) for p in marked]}"
        )

        in_platoon = [player for player in players if player.in_platoon]
        assert not in_platoon, f"EU replay should have no platoons, got: {in_platoon}"

        author_player = result.author
        assert author_player.frame_kind == "legendary"
        assert "avatar_bastille_legendary_anim" in author_player.avatar_url
        assert "profile_skin_gold_harvest" in author_player.profile_skin_url

        players_with_skin = [player for player in players if player.profile_skin_url]
        assert len(players_with_skin) >= 12, (
            f"expected most EU players to have profile skins, got {len(players_with_skin)}"
        )

        _log.info(f"Tests EU: replay extraction passed! author={result.author_nickname}, players={len(players)}")
        _log.info(
            "  marks: "
            + ", ".join(f"{p.nickname}={p.marks}" for p in sorted(players, key=lambda x: x.marks, reverse=True))
        )


def run() -> None:
    ReplayExtractionTest().run()
    ReplayKorbenPlatoonTest().run()
    ReplayEuExtractionTest().run()


if __name__ == "__main__":
    run()
