from .proto.battle_results_pb2 import (
    Author,
    Avatar,
    AvatarInfo,
    BattleResults,
    Player,
    PlayerInfo,
    PlayerResults,
    PlayerResultsInfo,
    RoomType as ProtoRoomType,
    TeamNumber as ProtoTeamNumber,
)
from .proto.update_arena_pb2 import ArenaPlayer, ArenaPlayers, UpdateArena

__all__ = [
    "ArenaPlayer",
    "ArenaPlayers",
    "Author",
    "Avatar",
    "AvatarInfo",
    "BattleResults",
    "Player",
    "PlayerInfo",
    "PlayerResults",
    "PlayerResultsInfo",
    "ProtoRoomType",
    "ProtoTeamNumber",
    "UpdateArena",
]
