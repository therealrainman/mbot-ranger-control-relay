from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar
from bleak import BleakClient

@dataclass
class MbotRanger:
    BLE_WRITE_UUID: ClassVar[str] = "0000ffe3-0000-1000-8000-00805f9b34fb"
    BLE_NOTIFY_UUID: ClassVar[str] = "0000ffe2-0000-1000-8000-00805f9b34fb"
    PACKET_HEADER: ClassVar[bytes] = bytes([0xFF, 0x55])
    PACKET_PREFIX: ClassVar[bytes] = bytes([0x07, 0x00, 0x02, 0x05])

    name: str
    address: str
    left_motor_speed: MotorSpeed = field(default_factory=lambda: MotorSpeed(raw=0))
    right_motor_speed: MotorSpeed = field(default_factory=lambda: MotorSpeed(raw=0))
    relay_client: BleakClient = field(init=False, repr=False)

    def __post_init__(self):
        self.relay_client = BleakClient(self.address)

    def __repr__(self):
        return f"MbotRanger(name={self.name}, address={self.address})"

    def set_motor_speeds_percent(self, left: float, right: float):
        self.left_motor_speed = MotorSpeed.from_percent(left)
        self.right_motor_speed = MotorSpeed.from_percent(right)

    async def send_to_relay(self):
        payload = MbotRanger.PACKET_HEADER + MbotRanger.PACKET_PREFIX + self.left_motor_speed.get_bytes() + self.right_motor_speed.get_bytes()
        print(f"    Sending: {payload.hex(' ').upper()}")
        await self.relay_client.write_gatt_char(MbotRanger.BLE_WRITE_UUID, payload, response=False)

    async def start_notify(self):
        await self.relay_client.start_notify(MbotRanger.BLE_NOTIFY_UUID, self.on_notify)

    async def stop_notify(self):
        await self.relay_client.stop_notify(MbotRanger.BLE_NOTIFY_UUID)

    async def print_characteristics(self):
        print("\n== BLE Services & Characteristics ===========================")
        for service in self.relay_client.services:
            print(f"\n  Service: {service.uuid}")
            for char in service.characteristics:
                props = ", ".join(char.properties)
                print(f"    Characteristic: {char.uuid}  [{props}]")
        print("=============================================================\n")

    @staticmethod
    def on_notify(_characteristic, data: bytearray):
        print(f"    Received: {data.hex(' ').upper()}")


@dataclass(frozen=True)
class MotorSpeed:
    raw: int  # Raw motor speed in the range [-255, 255]

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
