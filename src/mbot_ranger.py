from dataclasses import dataclass, field
from typing import Optional
from bleak import BleakClient
from constants import BLE_WRITE_UUID, PACKET_HEADER, PACKET_PREFIX
from motor_speed import MotorSpeed


@dataclass
class MbotRanger:
    name: str
    address: str
    left_motor_speed: MotorSpeed = MotorSpeed(raw=0)
    right_motor_speed: MotorSpeed = MotorSpeed(raw=0)
    relay_client: Optional[BleakClient] = field(default=None)
    gamepad_client: str = "tbdgamepadclient" # placeholder for eventual gamepad connection

    def __repr__(self):
        return f"MbotRanger(name={self.name}, address={self.address})"

    def initialize_relay_client(self):
        self.relay_client = BleakClient(self.address)

    def set_motor_speeds_percent(self, left: float, right: float):
        self.left_motor_speed = MotorSpeed.from_percent(left)
        self.right_motor_speed = MotorSpeed.from_percent(right)

    async def send_to_relay(self):
        if self.relay_client:
            payload = PACKET_HEADER + PACKET_PREFIX + self.left_motor_speed.get_bytes() + self.right_motor_speed.get_bytes()
            await self.relay_client.write_gatt_char(BLE_WRITE_UUID, payload, response=False)
        else:
            print(f"No relay client connected for {self}")
