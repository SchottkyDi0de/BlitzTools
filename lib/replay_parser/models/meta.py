import json
from dataclasses import dataclass
from typing import BinaryIO

from .enums import MapId


@dataclass
class Meta:
    player_name: str
    arena_unique_id: str
    battle_duration_secs: float
    tank_id: int
    map_id: MapId

    @classmethod
    def from_reader(cls, reader: BinaryIO) -> "Meta":
        payload = json.load(reader)
        map_id = MapId(payload["mapId"]) if payload["mapId"] in MapId._value2member_map_ else MapId.UNDEFINED
        return cls(
            player_name=payload["playerName"],
            arena_unique_id=payload["arenaUniqueId"],
            battle_duration_secs=payload["battleDuration"],
            tank_id=payload["vehicleCompDescriptor"],
            map_id=map_id,
        )
