from __future__ import annotations

from .models.region import Region
from .types import PlayerResultsInfo


def _parse_scalar_fields(data: bytes) -> dict[int, int]:
    pos = 0
    fields: dict[int, int] = {}

    while pos < len(data):
        tag, pos = _decode_varint(data, pos)
        field_number = tag >> 3
        wire_type = tag & 7

        if wire_type == 0:
            value, pos = _decode_varint(data, pos)
            fields[field_number] = value
        elif wire_type == 2:
            length, pos = _decode_varint(data, pos)
            pos += length
        elif wire_type == 5:
            pos += 4
        elif wire_type == 1:
            pos += 8
        else:
            break

    return fields


def _decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7
    raise ValueError("truncated varint")


def decode_marks_value(value: int | None) -> int:
    if value is None or value < 0:
        return 0
    if 1 <= value <= 3:
        return value
    if value >= 250:
        return min(value // 250, 3)
    return 0


def extract_marks_from_fields(region: Region, fields: dict[int, int]) -> int:
    values = [decode_marks_value(fields.get(110)), decode_marks_value(fields.get(124))]
    return max(values) if values else 0


def extract_marks(region: Region, result_info: PlayerResultsInfo) -> int:
    fields = _parse_scalar_fields(result_info.SerializeToString())
    values = [
        decode_marks_value(result_info.tank_marks) if _has_field(result_info, "tank_marks") else 0,
        decode_marks_value(fields.get(110)),
        decode_marks_value(result_info.marks_encoded) if _has_field(result_info, "marks_encoded") else 0,
        decode_marks_value(fields.get(124)),
    ]
    return max(values)


def player_info_marks(info) -> int:
    if _has_field(info, "marks"):
        return decode_marks_value(info.marks)
    return decode_marks_value(getattr(info, "marks", None))


def _has_field(message, name: str) -> bool:
    try:
        return message.HasField(name)
    except (AttributeError, ValueError):
        return False


def _direct_marks(value: int | None) -> int:
    return decode_marks_value(value)
