class ReplayParserError(Exception):
    pass


class InvalidMagicError(ReplayParserError):
    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual
        super().__init__(f"invalid magic: {actual:#x}, expected: {expected:#x}")


class PacketPayloadParsingError(ReplayParserError):
    def __init__(self, packet_type: int, clock_secs: float, source: Exception):
        self.packet_type = packet_type
        self.clock_secs = clock_secs
        self.source = source
        super().__init__(
            f"failed to parse type {packet_type} packet's payload at replay time {clock_secs}s"
        )
