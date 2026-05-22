#!/usr/bin/env python3
import asyncio
import pygame
from bleak import BleakScanner
from src.mbot_ranger import MbotRanger

MBOT_NAME_KEYWORDS = ["makeblock", "mbot", "ranger"]
SCAN_TIMEOUT = 5  # seconds
DEADZONE = 0.1
REFRESH_RATE = 0.05  # 20Hz update rate

async def find_mbot():
    print(f"Scanning for mBot Ranger ({SCAN_TIMEOUT}s)...")
    devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
    for device in devices:
        name = (device.name or "").lower()
        if any(kw in name for kw in MBOT_NAME_KEYWORDS):
            return device
    return None

def apply_deadzone(value, deadzone):
    if abs(value) < deadzone:
        return 0.0
    return value

async def joystick_loop(ranger: MbotRanger):
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("❌ No joystick detected. Please connect a controller.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"✅ Joystick detected: {joystick.get_name()}")

    print("\nControl layout:")
    print(" - Left Stick Y: Forward / Backward")
    print(" - Right Stick X: Left / Right (Turning)")
    print(" - Press 'B' button or Ctrl+C to exit")

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Exit on button 1 (usually 'B' on Xbox or 'Circle' on PS)
                    if event.button == 1:
                        running = False

            # Get axis values
            # Left stick Y (axis 1) for throttle
            # Right stick X (axis 2 or 3 depending on controller) for steering
            # Most modern controllers:
            # Axis 0: Left Stick X
            # Axis 1: Left Stick Y
            # Axis 2: Right Stick X (sometimes 3)
            # Axis 3: Right Stick Y (sometimes 4)

            throttle = -joystick.get_axis(1) # Negate because Y is usually inverted
            steering = joystick.get_axis(2) if joystick.get_numaxes() > 2 else joystick.get_axis(0)

            throttle = apply_deadzone(throttle, DEADZONE)
            steering = apply_deadzone(steering, DEADZONE)

            # Arcade drive mapping
            left_speed = (throttle + steering) * 100
            right_speed = (throttle - steering) * 100

            # Clamp to [-100, 100]
            left_speed = max(-100, min(100, left_speed))
            right_speed = max(-100, min(100, right_speed))

            # Note: mBot Ranger might need inverted signs depending on motor orientation
            # Based on main.py:
            # Forward: left=-50, right=50
            # Backward: left=50, right=-50
            # So for forward (throttle > 0): left should be negative, right positive.

            ranger.set_motor_speeds_percent(left=-left_speed, right=right_speed)
            await ranger.send_to_relay()

            await asyncio.sleep(REFRESH_RATE)

    except asyncio.CancelledError:
        pass
    finally:
        print("\nStopping mBot...")
        ranger.set_motor_speeds_percent(0, 0)
        await ranger.send_to_relay()
        pygame.quit()

async def main():
    print("=== mBot Ranger Joystick Control ===\n")

    device = await find_mbot()
    if device is None:
        print("❌ mBot Ranger not found.")
        return

    print(f"✅ Found:   {device.name} ({device.address})")

    ranger = MbotRanger(name=str(device.name), address=device.address)
    ranger.initialize_relay_client()

    print(f"\nConnecting...")
    async with ranger.relay_client:
        print(f"✅ Connected!\n")
        await joystick_loop(ranger)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
