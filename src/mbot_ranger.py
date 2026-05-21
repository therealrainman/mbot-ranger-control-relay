from dataclasses import dataclass, field
from typing import Optional
from bleak import BleakClient
from src.constants import BLE_WRITE_UUID, BLE_NOTIFY_UUID, PACKET_HEADER, PACKET_PREFIX
from src.motor_speed import MotorSpeed

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
        if not self.relay_client:
            self.relay_client = BleakClient(self.address)
        else:
            print(f"Relay client already initialized for {self}")

    def set_motor_speeds_percent(self, left: float, right: float):
        self.left_motor_speed = MotorSpeed.from_percent(left)
        self.right_motor_speed = MotorSpeed.from_percent(right)

    async def send_to_relay(self):
        if self.relay_client and self.relay_client.is_connected:
            payload = PACKET_HEADER + PACKET_PREFIX + self.left_motor_speed.get_bytes() + self.right_motor_speed.get_bytes()
            print(f"    Sending: {payload.hex(' ').upper()}")
            await self.relay_client.write_gatt_char(BLE_WRITE_UUID, payload, response=False)
        else:
            print(f"Relay client not connected for {self}")

    async def start_notify(self):
        if self.relay_client:
            await self.relay_client.start_notify(BLE_NOTIFY_UUID, self.on_notify)

    async def stop_notify(self):
        if self.relay_client:
            await self.relay_client.stop_notify(BLE_NOTIFY_UUID)

    async def print_characteristics(self):
        if self.relay_client and self.relay_client.is_connected:
            print("\n── BLE Services & Characteristics ───────────────────────────")
            for service in self.relay_client.services:
                print(f"\n  Service: {service.uuid}")
                for char in service.characteristics:
                    props = ", ".join(char.properties)
                    print(f"    Characteristic: {char.uuid}  [{props}]")
            print("─────────────────────────────────────────────────────────────\n")
        else:
            print(f"Relay client not connected for {self}")

    @staticmethod
    def on_notify(characteristic, data: bytearray):
        print(f"    Received: {data.hex(' ').upper()}")
