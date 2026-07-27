from dataclasses import dataclass
from typing import BinaryIO

from . import binary_io
from .packet import Packet


@dataclass
class Data:
    client_version: str
    packets: list[Packet]

    @classmethod
    def from_reader(cls, reader: BinaryIO) -> "Data":
        magic = binary_io.read_u32(reader)
        binary_io.assert_magic(magic, 0x12345678)

        binary_io.read_u64(reader)
        binary_io.read_length_delimited(reader)
        client_version = binary_io.read_string(reader)
        binary_io.read_u8(reader)

        packets: list[Packet] = []
        while (packet := Packet.from_reader(reader)) is not None:
            packets.append(packet)

        return cls(client_version=client_version, packets=packets)
