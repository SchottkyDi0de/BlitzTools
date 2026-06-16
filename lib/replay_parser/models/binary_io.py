import io
import pickle
import struct
from typing import BinaryIO

from ..errors import InvalidMagicError


def assert_magic(actual: int, expected: int) -> None:
    if actual != expected:
        raise InvalidMagicError(expected=expected, actual=actual)


def read_length_delimited(reader: BinaryIO) -> bytes:
    length = reader.read(1)[0]
    return reader.read(length)


def read_string(reader: BinaryIO) -> str:
    return read_length_delimited(reader).decode("utf-8")


def read_quirky_length(reader: BinaryIO) -> int:
    first = reader.read(1)[0]
    if first == 0xFF:
        length = struct.unpack("<H", reader.read(2))[0]
        assert_magic(reader.read(1)[0], 0x00)
        return length
    return first


def read_pickled(reader: BinaryIO, length: int):
    buffer = io.BytesIO(reader.read(length))
    return pickle.load(buffer, encoding="bytes")


def read_u32(reader: BinaryIO) -> int:
    return struct.unpack("<I", reader.read(4))[0]


def read_u64(reader: BinaryIO) -> int:
    return struct.unpack("<Q", reader.read(8))[0]


def read_f32(reader: BinaryIO) -> float:
    return struct.unpack("<f", reader.read(4))[0]


def read_u8(reader: BinaryIO) -> int:
    return reader.read(1)[0]
