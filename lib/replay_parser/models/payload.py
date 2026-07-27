from dataclasses import dataclass

from ..errors import PacketPayloadParsingError
from . import binary_io
from .base_player_create import BasePlayerCreate
from .entity_method import EntityMethod, UnknownEntityMethod, UpdateArenaMethod, parse_entity_method


@dataclass
class BasePlayerCreatePayload:
    author_nickname: str
    arena_unique_id: int
    arena_type_id: int
    arguments: BasePlayerCreate


@dataclass
class EntityMethodPayload:
    method: EntityMethod


@dataclass
class UnknownPayload:
    packet_type: int


Payload = BasePlayerCreatePayload | EntityMethodPayload | UnknownPayload


def parse_payload(packet_type: int, raw_payload: bytes, clock_secs: float) -> Payload:
    try:
        return _parse_payload(packet_type, raw_payload)
    except Exception as exc:
        raise PacketPayloadParsingError(packet_type, clock_secs, exc) from exc


def _parse_payload(packet_type: int, raw_payload: bytes) -> Payload:
    import io

    reader = io.BytesIO(raw_payload)

    if packet_type == 0:
        reader.read(10)
        author_nickname = binary_io.read_string(reader)
        arena_unique_id = binary_io.read_u64(reader)
        arena_type_id = binary_io.read_u32(reader)
        pickled_length = binary_io.read_quirky_length(reader)
        arguments = BasePlayerCreate.from_pickled(binary_io.read_pickled(reader, pickled_length))
        return BasePlayerCreatePayload(
            author_nickname=author_nickname,
            arena_unique_id=arena_unique_id,
            arena_type_id=arena_type_id,
            arguments=arguments,
        )

    if packet_type == 8:
        return EntityMethodPayload(method=parse_entity_method(raw_payload))

    return UnknownPayload(packet_type=packet_type)
