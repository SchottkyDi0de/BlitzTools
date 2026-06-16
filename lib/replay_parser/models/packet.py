import struct
from dataclasses import dataclass
from typing import BinaryIO

from . import binary_io
from .payload import Payload, parse_payload


@dataclass
class Packet:
    clock_secs: float
    payload: Payload

    @classmethod
    def from_reader(cls, reader: BinaryIO) -> "Packet | None":
        header = reader.read(4)
        if len(header) < 4:
            return None

        length = struct.unpack("<I", header)[0]
        packet_type = binary_io.read_u32(reader)
        clock_secs = binary_io.read_f32(reader)
        raw_payload = reader.read(length)
        payload = parse_payload(packet_type, raw_payload, clock_secs)
        return cls(clock_secs=clock_secs, payload=payload)
