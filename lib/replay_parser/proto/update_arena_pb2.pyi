from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UpdateArena(_message.Message):
    __slots__ = ("players",)
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    players: ArenaPlayers
    def __init__(self, players: _Optional[_Union[ArenaPlayers, _Mapping]] = ...) -> None: ...

class ArenaPlayers(_message.Message):
    __slots__ = ("players",)
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    players: _containers.RepeatedCompositeFieldContainer[ArenaPlayer]
    def __init__(self, players: _Optional[_Iterable[_Union[ArenaPlayer, _Mapping]]] = ...) -> None: ...

class ArenaPlayer(_message.Message):
    __slots__ = ("nickname", "team_number", "account_id", "clan_tag", "platoon_number")
    NICKNAME_FIELD_NUMBER: _ClassVar[int]
    TEAM_NUMBER_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    CLAN_TAG_FIELD_NUMBER: _ClassVar[int]
    PLATOON_NUMBER_FIELD_NUMBER: _ClassVar[int]
    nickname: str
    team_number: int
    account_id: int
    clan_tag: str
    platoon_number: int
    def __init__(self, nickname: _Optional[str] = ..., team_number: _Optional[int] = ..., account_id: _Optional[int] = ..., clan_tag: _Optional[str] = ..., platoon_number: _Optional[int] = ...) -> None: ...
