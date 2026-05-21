#!/usr/bin/env python3
"""
mBot Ranger — BLE simple demo with response notifications
Forward at 50% for 2s, pause 5s, backward at 50% for 2s.
Subscribes to the notify characteristic and prints all incoming bytes.
"""
import asyncio
from bleak import BleakScanner
from src.mbot_ranger import MbotRanger

MBOT_NAME_KEYWORDS = ["makeblock", "mbot", "ranger"]
SCAN_TIMEOUT       = 5   # seconds


# ── BLE helpers ───────────────────────────────────────────────────────────────

async def find_mbot():
    print(f"Scanning for mBot Ranger ({SCAN_TIMEOUT}s)...")
    devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
    for device in devices:
        name = (device.name or "").lower()
        if any(kw in name for kw in MBOT_NAME_KEYWORDS):
            return device
    return None

# ── Demo ──────────────────────────────────────────────────────────────────────

async def run_demo(ranger: MbotRanger):
    if ranger.relay_client is None:
        print("❌ Relay client is not initialized.")
        return
    await ranger.print_characteristics()

    # Subscribe to notifications
    print("Subscribing to notifications...")
    await ranger.start_notify()
    print("✅ Subscribed — incoming bytes will be printed as they arrive\n")

    # Forward
    print(f"▶  Forward at 50% for 2 seconds...")
    ranger.set_motor_speeds_percent(left=-50, right=50)
    await ranger.send_to_relay()
    await asyncio.sleep(2.0)

    # Stop
    ranger.set_motor_speeds_percent(left=0, right=0)
    await ranger.send_to_relay()
    print("   Pausing for 5 seconds...\n")
    await asyncio.sleep(5.0)

    # Backward
    print(f"◀  Backward at 50% for 2 seconds...")
    ranger.set_motor_speeds_percent(left=50, right=-50)
    await ranger.send_to_relay()
    await asyncio.sleep(2.0)

    # Final stop
    ranger.set_motor_speeds_percent(left=0, right=0)
    await ranger.send_to_relay()

    # Unsubscribe cleanly
    await ranger.stop_notify()
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

    ranger = MbotRanger(name=str(device.name), address=device.address)
    ranger.initialize_relay_client()

    if ranger.relay_client is None:
        print("❌ Failed to initialize BLE client.")
        return

    print(f"\nConnecting...")
    async with ranger.relay_client:
        print(f"✅ Connected! (MTU: {ranger.relay_client.mtu_size})\n")
        await run_demo(ranger)


if __name__ == "__main__":
    asyncio.run(main())
