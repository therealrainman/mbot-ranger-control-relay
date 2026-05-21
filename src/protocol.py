class Packet(bytes):
    """A raw BLE command packet."""

    @staticmethod
    def _int16_le(v: int) -> bytes:
        """Pack a signed integer as a little-endian 16-bit value."""
        v = max(-255, min(255, v))
        if v < 0:
            v = 0x10000 + v
        return bytes([v & 0xFF, (v >> 8) & 0xFF])

    @classmethod
    def motor(cls, left: int, right: int) -> "Packet":
        """
        Build a dual-motor drive packet.
        Positive = forward, negative = backward.
        Motor 1 (left) is wired in reverse so is negated internally.
        """
        payload = bytes([0x07, 0x00, 0x02, 0x05]) + cls._int16_le(-left) + cls._int16_le(right)
        return cls(bytes([0xFF, 0x55]) + payload)

    @classmethod
    def stop(cls) -> "Packet":
        return cls.motor(0, 0)

    @staticmethod
    def fmt(data: bytes) -> str:
        """Format bytes as uppercase hex pairs e.g. FF 55 07 ..."""
        return data.hex(' ').upper()
