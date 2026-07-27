from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TeamNumber(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TEAM_NUMBER_UNSPECIFIED: _ClassVar[TeamNumber]
    ONE: _ClassVar[TeamNumber]
    TWO: _ClassVar[TeamNumber]

class RoomType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ANY: _ClassVar[RoomType]
    REGULAR: _ClassVar[RoomType]
    TRAINING_ROOM: _ClassVar[RoomType]
    TOURNAMENT: _ClassVar[RoomType]
    QUICK_TOURNAMENT: _ClassVar[RoomType]
    RATING: _ClassVar[RoomType]
    MAD_GAMES: _ClassVar[RoomType]
    REALISTIC_BATTLES: _ClassVar[RoomType]
    UPRISING: _ClassVar[RoomType]
    GRAVITY_MODE: _ClassVar[RoomType]
    SKIRMISH: _ClassVar[RoomType]
    BURNING_GAMES: _ClassVar[RoomType]
TEAM_NUMBER_UNSPECIFIED: TeamNumber
ONE: TeamNumber
TWO: TeamNumber
ANY: RoomType
REGULAR: RoomType
TRAINING_ROOM: RoomType
TOURNAMENT: RoomType
QUICK_TOURNAMENT: RoomType
RATING: RoomType
MAD_GAMES: RoomType
REALISTIC_BATTLES: RoomType
UPRISING: RoomType
GRAVITY_MODE: RoomType
SKIRMISH: RoomType
BURNING_GAMES: RoomType

class AvatarInfo(_message.Message):
    __slots__ = ("gfx_url", "gfx2_url", "kind")
    GFX_URL_FIELD_NUMBER: _ClassVar[int]
    GFX2_URL_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    gfx_url: str
    gfx2_url: str
    kind: str
    def __init__(self, gfx_url: _Optional[str] = ..., gfx2_url: _Optional[str] = ..., kind: _Optional[str] = ...) -> None: ...

class Avatar(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: AvatarInfo
    def __init__(self, info: _Optional[_Union[AvatarInfo, _Mapping]] = ...) -> None: ...

class PlayerInfo(_message.Message):
    __slots__ = ("nickname", "platoon_id", "team", "clan_tag", "avatar", "rank", "marks", "tank_id")
    NICKNAME_FIELD_NUMBER: _ClassVar[int]
    PLATOON_ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_FIELD_NUMBER: _ClassVar[int]
    CLAN_TAG_FIELD_NUMBER: _ClassVar[int]
    AVATAR_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    MARKS_FIELD_NUMBER: _ClassVar[int]
    TANK_ID_FIELD_NUMBER: _ClassVar[int]
    nickname: str
    platoon_id: int
    team: TeamNumber
    clan_tag: str
    avatar: Avatar
    rank: int
    marks: int
    tank_id: int
    def __init__(self, nickname: _Optional[str] = ..., platoon_id: _Optional[int] = ..., team: _Optional[_Union[TeamNumber, str]] = ..., clan_tag: _Optional[str] = ..., avatar: _Optional[_Union[Avatar, _Mapping]] = ..., rank: _Optional[int] = ..., marks: _Optional[int] = ..., tank_id: _Optional[int] = ...) -> None: ...

class Player(_message.Message):
    __slots__ = ("account_id", "info")
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    account_id: int
    info: PlayerInfo
    def __init__(self, account_id: _Optional[int] = ..., info: _Optional[_Union[PlayerInfo, _Mapping]] = ...) -> None: ...

class PlayerResultsInfo(_message.Message):
    __slots__ = ("credits_earned", "base_xp", "n_shots", "n_hits_dealt", "n_penetrations_dealt", "damage_dealt", "damage_assisted_1", "damage_assisted_2", "n_hits_received", "n_non_penetrating_hits_received", "n_penetrations_received", "n_enemies_damaged", "n_enemies_destroyed", "victory_points_earned", "victory_points_seized", "account_id", "tank_id", "mm_rating", "damage_blocked", "tank_marks", "marks_encoded")
    CREDITS_EARNED_FIELD_NUMBER: _ClassVar[int]
    BASE_XP_FIELD_NUMBER: _ClassVar[int]
    N_SHOTS_FIELD_NUMBER: _ClassVar[int]
    N_HITS_DEALT_FIELD_NUMBER: _ClassVar[int]
    N_PENETRATIONS_DEALT_FIELD_NUMBER: _ClassVar[int]
    DAMAGE_DEALT_FIELD_NUMBER: _ClassVar[int]
    DAMAGE_ASSISTED_1_FIELD_NUMBER: _ClassVar[int]
    DAMAGE_ASSISTED_2_FIELD_NUMBER: _ClassVar[int]
    N_HITS_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    N_NON_PENETRATING_HITS_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    N_PENETRATIONS_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    N_ENEMIES_DAMAGED_FIELD_NUMBER: _ClassVar[int]
    N_ENEMIES_DESTROYED_FIELD_NUMBER: _ClassVar[int]
    VICTORY_POINTS_EARNED_FIELD_NUMBER: _ClassVar[int]
    VICTORY_POINTS_SEIZED_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    TANK_ID_FIELD_NUMBER: _ClassVar[int]
    MM_RATING_FIELD_NUMBER: _ClassVar[int]
    DAMAGE_BLOCKED_FIELD_NUMBER: _ClassVar[int]
    TANK_MARKS_FIELD_NUMBER: _ClassVar[int]
    MARKS_ENCODED_FIELD_NUMBER: _ClassVar[int]
    credits_earned: int
    base_xp: int
    n_shots: int
    n_hits_dealt: int
    n_penetrations_dealt: int
    damage_dealt: int
    damage_assisted_1: int
    damage_assisted_2: int
    n_hits_received: int
    n_non_penetrating_hits_received: int
    n_penetrations_received: int
    n_enemies_damaged: int
    n_enemies_destroyed: int
    victory_points_earned: int
    victory_points_seized: int
    account_id: int
    tank_id: int
    mm_rating: float
    damage_blocked: int
    tank_marks: int
    marks_encoded: int
    def __init__(self, credits_earned: _Optional[int] = ..., base_xp: _Optional[int] = ..., n_shots: _Optional[int] = ..., n_hits_dealt: _Optional[int] = ..., n_penetrations_dealt: _Optional[int] = ..., damage_dealt: _Optional[int] = ..., damage_assisted_1: _Optional[int] = ..., damage_assisted_2: _Optional[int] = ..., n_hits_received: _Optional[int] = ..., n_non_penetrating_hits_received: _Optional[int] = ..., n_penetrations_received: _Optional[int] = ..., n_enemies_damaged: _Optional[int] = ..., n_enemies_destroyed: _Optional[int] = ..., victory_points_earned: _Optional[int] = ..., victory_points_seized: _Optional[int] = ..., account_id: _Optional[int] = ..., tank_id: _Optional[int] = ..., mm_rating: _Optional[float] = ..., damage_blocked: _Optional[int] = ..., tank_marks: _Optional[int] = ..., marks_encoded: _Optional[int] = ...) -> None: ...

class PlayerResults(_message.Message):
    __slots__ = ("result_id", "info")
    RESULT_ID_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    result_id: int
    info: PlayerResultsInfo
    def __init__(self, result_id: _Optional[int] = ..., info: _Optional[_Union[PlayerResultsInfo, _Mapping]] = ...) -> None: ...

class Author(_message.Message):
    __slots__ = ("hitpoints_left", "total_credits", "total_xp", "n_shots", "n_hits", "n_splashes", "n_penetrations", "damage_dealt", "account_id", "team_number")
    HITPOINTS_LEFT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CREDITS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_XP_FIELD_NUMBER: _ClassVar[int]
    N_SHOTS_FIELD_NUMBER: _ClassVar[int]
    N_HITS_FIELD_NUMBER: _ClassVar[int]
    N_SPLASHES_FIELD_NUMBER: _ClassVar[int]
    N_PENETRATIONS_FIELD_NUMBER: _ClassVar[int]
    DAMAGE_DEALT_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_NUMBER_FIELD_NUMBER: _ClassVar[int]
    hitpoints_left: int
    total_credits: int
    total_xp: int
    n_shots: int
    n_hits: int
    n_splashes: int
    n_penetrations: int
    damage_dealt: int
    account_id: int
    team_number: TeamNumber
    def __init__(self, hitpoints_left: _Optional[int] = ..., total_credits: _Optional[int] = ..., total_xp: _Optional[int] = ..., n_shots: _Optional[int] = ..., n_hits: _Optional[int] = ..., n_splashes: _Optional[int] = ..., n_penetrations: _Optional[int] = ..., damage_dealt: _Optional[int] = ..., account_id: _Optional[int] = ..., team_number: _Optional[_Union[TeamNumber, str]] = ...) -> None: ...

class BattleResults(_message.Message):
    __slots__ = ("mode_map_id", "timestamp_secs", "winner_team_number", "author", "room_type", "free_xp", "players", "player_results")
    MODE_MAP_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_SECS_FIELD_NUMBER: _ClassVar[int]
    WINNER_TEAM_NUMBER_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    ROOM_TYPE_FIELD_NUMBER: _ClassVar[int]
    FREE_XP_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    PLAYER_RESULTS_FIELD_NUMBER: _ClassVar[int]
    mode_map_id: int
    timestamp_secs: int
    winner_team_number: TeamNumber
    author: Author
    room_type: RoomType
    free_xp: int
    players: _containers.RepeatedCompositeFieldContainer[Player]
    player_results: _containers.RepeatedCompositeFieldContainer[PlayerResults]
    def __init__(self, mode_map_id: _Optional[int] = ..., timestamp_secs: _Optional[int] = ..., winner_team_number: _Optional[_Union[TeamNumber, str]] = ..., author: _Optional[_Union[Author, _Mapping]] = ..., room_type: _Optional[_Union[RoomType, str]] = ..., free_xp: _Optional[int] = ..., players: _Optional[_Iterable[_Union[Player, _Mapping]]] = ..., player_results: _Optional[_Iterable[_Union[PlayerResults, _Mapping]]] = ...) -> None: ...
