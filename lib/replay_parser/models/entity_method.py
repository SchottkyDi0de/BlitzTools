import io
from dataclasses import dataclass

from ..proto import update_arena_pb2
from . import binary_io
from .base_player_create import BasePlayerCreate


@dataclass
class UpdateArenaMethod:
    field_number: int
    arguments: update_arena_pb2.UpdateArena


@dataclass
class UnknownEntityMethod:
    sub_type: int


EntityMethod = UpdateArenaMethod | UnknownEntityMethod


def parse_entity_method(raw_payload: bytes) -> EntityMethod:
    reader = io.BytesIO(raw_payload)
    binary_io.read_u32(reader)
    sub_type = binary_io.read_u32(reader)

    if sub_type != 47:
        return UnknownEntityMethod(sub_type=sub_type)

    binary_io.read_u32(reader)
    field_number = _decode_varint(reader)
    message_length = binary_io.read_quirky_length(reader)
    message_bytes = reader.read(message_length)
    arguments = update_arena_pb2.UpdateArena()
    arguments.ParseFromString(message_bytes)
    return UpdateArenaMethod(field_number=field_number, arguments=arguments)


def _decode_varint(reader) -> int:
    result = 0
    shift = 0
    while True:
        byte = reader.read(1)[0]
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result
        shift += 7
