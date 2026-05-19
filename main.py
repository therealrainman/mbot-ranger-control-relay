#!/usr/bin/env python3
"""
mBot Ranger — BLE simple demo with response notifications
Forward at 50% for 2s, pause 5s, backward at 50% for 2s.
Subscribes to the notify characteristic and prints all incoming bytes.
"""

import asyncio
from bleak import BleakScanner, BleakClient

MBOT_NAME_KEYWORDS = ["makeblock", "mbot", "ranger"]
SCAN_TIMEOUT       = 10   # seconds
SPEED_50           = int(255 * 0.50)

# Known Makeblock BLE characteristic UUID for sending commands
# (we will discover and print all of them regardless)
WRITE_UUID  = "0000ffe3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"


# ── Protocol helpers ──────────────────────────────────────────────────────────

def int16_le(v: int) -> bytes:
    """Pack a signed integer as a little-endian 16-bit value."""
    v = max(-255, min(255, v))
    if v < 0:
        v = 0x10000 + v
    return bytes([v & 0xFF, (v >> 8) & 0xFF])


def motor_packet(left: int, right: int) -> bytes:
    """
    Build a dual-motor drive packet.
    Positive = forward, negative = backward.
    Motor 1 (left) is wired in reverse so is negated internally.
    """
    payload = bytes([0x07, 0x00, 0x02, 0x05]) + int16_le(-left) + int16_le(right)
    return bytes([0xFF, 0x55]) + payload


def stop_packet() -> bytes:
    return motor_packet(0, 0)


def fmt(data: bytes) -> str:
    """Format bytes as uppercase hex pairs e.g. FF 55 07 ..."""
    return data.hex(' ').upper()


# ── Notification handler ──────────────────────────────────────────────────────

def on_notify(characteristic, data: bytearray):
    print(f"  📨 Received: {fmt(bytes(data))}")


# ── BLE helpers ───────────────────────────────────────────────────────────────

async def find_mbot():
    print(f"Scanning for mBot Ranger ({SCAN_TIMEOUT}s)...")
    devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
    for device in devices:
        name = (device.name or "").lower()
        if any(kw in name for kw in MBOT_NAME_KEYWORDS):
            return device
    return None


async def print_characteristics(client: BleakClient):
    print("\n── BLE Services & Characteristics ───────────────────────────")
    for service in client.services:
        print(f"\n  Service: {service.uuid}")
        for char in service.characteristics:
            props = ", ".join(char.properties)
            print(f"    Characteristic: {char.uuid}  [{props}]")
    print("─────────────────────────────────────────────────────────────\n")


async def send(client: BleakClient, packet: bytes, label: str):
    print(f"{label}")
    print(f"  Bytes: {fmt(packet)}")
    await client.write_gatt_char(WRITE_UUID, packet, response=False)
    print(f"  ✅ Sent\n")


async def send_stop(client: BleakClient):
    """Send stop twice with a short gap, then wait for BLE to flush."""
    await send(client, stop_packet(), "⏹  Stopping...")
    await asyncio.sleep(0.1)
    await send(client, stop_packet(), "⏹  Stop (repeat)...")
    await asyncio.sleep(0.5)


# ── Demo ──────────────────────────────────────────────────────────────────────

async def run_demo(client: BleakClient):
    await print_characteristics(client)

    # Subscribe to notifications
    print("Subscribing to notifications...")
    await client.start_notify(NOTIFY_UUID, on_notify)
    print("✅ Subscribed — incoming bytes will be printed as they arrive\n")

    # Forward
    await send(client, motor_packet(SPEED_50, SPEED_50),
               f"▶  Forward at 50% ({SPEED_50}/255) for 2 seconds...")
    await asyncio.sleep(2.0)

    # Stop
    await send_stop(client)
    print("   Pausing for 5 seconds...\n")
    await asyncio.sleep(5.0)

    # Backward
    await send(client, motor_packet(-SPEED_50, -SPEED_50),
               f"◀  Backward at 50% ({SPEED_50}/255) for 2 seconds...")
    await asyncio.sleep(2.0)

    # Stop
    await send_stop(client)

    # Unsubscribe cleanly
    await client.stop_notify(NOTIFY_UUID)
    print("✅ Demo complete!")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("=== mBot Ranger — BLE Demo with response notifications ===\n")

    device = await find_mbot()
    if device is None:
        print("❌ mBot Ranger not found. Make sure it is powered on and in range.")
        return

    print(f"✅ Found:   {device.name}")
    print(f"   Address: {device.address}")
    print(f"\nConnecting...")

    async with BleakClient(device.address) as client:
        print(f"✅ Connected! (MTU: {client.mtu_size})\n")
        await run_demo(client)


if __name__ == "__main__":
    asyncio.run(main())
