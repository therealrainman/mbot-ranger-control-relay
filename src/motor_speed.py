from dataclasses import dataclass


@dataclass(frozen=True)
class MotorSpeed:
    raw: int  # [-255, 255] — the single source of truth

    def __post_init__(self):
        if not -255 <= self.raw <= 255:
            raise ValueError(f"raw must be in [-255, 255], got {self.raw}")

    def __repr__(self) -> str:
        return f"MotorSpeed(raw={self.raw}, percent={self.percent})"

    @property
    def percent(self) -> float:
        return round((self.raw / 255) * 100, 1)

    @classmethod
    def from_percent(cls, percent: float) -> MotorSpeed:
        if not -100 <= percent <= 100:
            raise ValueError(f"percent must be in [-100, 100], got {percent}")
        return cls(raw=int((percent / 100) * 255))

    def get_bytes(self) -> bytes:
        """Pack a signed integer as a little-endian 16-bit value."""
        signed_speed = self.raw if self.raw >= 0 else 0x10000 + self.raw
        return bytes([signed_speed & 0xFF, (signed_speed >> 8) & 0xFF])
