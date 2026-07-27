import pickle
from dataclasses import dataclass
from typing import BinaryIO

from ..marks import extract_marks, player_info_marks
from ..models.region import Region
from ..types import BattleResults


@dataclass
class BattleResultsDat:
    arena_unique_id: int
    buffer: bytes

    @classmethod
    def from_reader(cls, reader: BinaryIO) -> "BattleResultsDat":
        arena_unique_id, buffer = pickle.load(reader, encoding="bytes")
        return cls(arena_unique_id=arena_unique_id, buffer=buffer)

    def decode(self, region: Region = Region.EU) -> BattleResults:
        message = BattleResults()
        message.ParseFromString(self.buffer)
        _enrich_player_info(message, region)
        return message


def _enrich_player_info(battle_results: BattleResults, region: Region) -> None:
    results_by_account = {
        result.info.account_id: result.info for result in battle_results.player_results
    }

    for player in battle_results.players:
        result_info = results_by_account.get(player.account_id)
        if result_info is None:
            player.info.marks = 0
            continue

        player.info.tank_id = result_info.tank_id
        player.info.marks = max(extract_marks(region, result_info), player_info_marks(player.info))
