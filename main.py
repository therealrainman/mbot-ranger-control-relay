#!/usr/bin/env python3
from __future__ import annotations

import sys
# Set coinit_flags before any COM-related imports to ensure MTA on Windows
sys.coinit_flags = 0  # 0 means MTA

import asyncio

import pygame
# On Windows, pygame or other modules might initialize COM as STA (Single Threaded Apartment),
# which can break Bleak's callbacks. We try to uninitialize it to allow MTA.
if sys.platform == "win32":
    try:
        from bleak.backends.winrt.util import uninitialize_sta
        uninitialize_sta()
    except (ImportError, AttributeError):
        pass

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from src.gamepad_manager import GamepadManager
from src.mbot_ranger import MbotRanger

BUMPERBOTS_NAME_ID_MAP = {
    "Blue": "Makeblock_LE703e97e38098",
    "Red": "Makeblock_LE10a56269e063",
    # "Green": "Makeblock_LE003",
    # "Yellow": "Makeblock_LE004",
}

SCAN_TIMEOUT = 5  # seconds


# == Discovery ================================================================


async def scan_for_devices() -> dict[str, BLEDevice]:
    """Scan and return a map of device_name → BLEDevice for all found devices."""
    target_names = set(BUMPERBOTS_NAME_ID_MAP.values())
    print(f"Scanning for {len(target_names)} device(s) ({SCAN_TIMEOUT}s)...")

    discovered = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
    found: dict[str, BLEDevice] = {}

    for device in discovered:
        if device.name in target_names:
            color = next(
                color
                for color, name in BUMPERBOTS_NAME_ID_MAP.items()
                if name == device.name
            )
            found[color] = device

    return found


def verify_discovery(found: dict[str, BLEDevice]) -> bool:
    """Print a discovery report. Returns True if all devices were found."""
    all_found = True
    for color, device_name in BUMPERBOTS_NAME_ID_MAP.items():
        if color in found:
            print(f"  ✅ {color}: {device_name} ({found[color].address})")
        else:
            print(f"  ❌ {color}: {device_name} — not found")
            all_found = False
    return all_found


def verify_controllers(required: int) -> bool:
    """Check that enough controllers are connected. Returns True if sufficient."""
    available = pygame.joystick.get_count()
    if available >= required:
        print(f"  ✅ {available} controller(s) detected ({required} required)")
        return True
    else:
        print(
            f"  ❌ {available} controller(s) detected, but {required} required. "
            "Please connect more controllers and try again."
        )
        return False


# == Pairing ==================================================================


async def wait_for_button_press(
    button: int, prompt: str, timeout: float = 30.0
) -> int | None:
    print(prompt)
    deadline = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < deadline:
        pygame.event.pump()  # ← flush pygame's internal event queue
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == button:
                return event.joy
        await asyncio.sleep(0.05)

    return None


async def pair_controllers(colors: list[str]) -> dict[str, int] | None:
    """
    Interactively pair each color robot to a controller.
    Returns a map of color → joystick_index, or None if pairing failed.
    """
    # Initialize all joysticks so they start generating events
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for j in joysticks:
        j.init()

    pygame.event.clear()  # Clear any stale events before pairing

    pairings: dict[str, int] = {}
    used_joysticks: set[int] = set()

    for color in colors:
        while True:
            joystick_index = await wait_for_button_press(
                button=0,  # 'A' on Xbox, 'Cross' on PS
                prompt=f"\n🎮 Press 'A' on the controller for [{color}]...",
            )

            if joystick_index is None:
                print(f"  ❌ Timed out waiting for [{color}]. Aborting setup.")
                return None

            if joystick_index in used_joysticks:
                print(
                    f"  ⚠️  Controller {joystick_index} is already paired. "
                    "Try a different controller."
                )
                continue

            used_joysticks.add(joystick_index)
            pairings[color] = joystick_index
            print(f"  ✅ Controller {joystick_index} paired to [{color}]")
            break

    return pairings


# == Main =====================================================================


async def main():
    print("=== Bumperbots Multi-Robot Controller ===\n")

    pygame.init()
    pygame.joystick.init()

    # Re-verify MTA on Windows after pygame initialization
    if sys.platform == "win32":
        try:
            from bleak.backends.winrt.util import uninitialize_sta
            uninitialize_sta()
        except (ImportError, AttributeError):
            pass

    # 1. Scan for all robots
    print("[ Step 1 / 3 ] Scanning for robots...")
    found_devices = await scan_for_devices()
    if not verify_discovery(found_devices):
        print("\n❌ Not all robots were found. Please check they are powered on.")
        pygame.quit()
        return

    colors = list(found_devices.keys())

    # 2. Verify enough controllers
    print("\n[ Step 2 / 3 ] Checking controllers...")
    if not verify_controllers(required=len(colors)):
        pygame.quit()
        return

    # 3. Interactive pairing
    print("\n[ Step 3 / 3 ] Pairing controllers to robots...")
    pairings = await pair_controllers(colors)
    if pairings is None:
        pygame.quit()
        return

    # Build GamepadManagers
    managers = [
        GamepadManager(
            ranger=MbotRanger(
                name=color,
                address=found_devices[color].address,
            )
        )
        for color in colors
    ]

    for manager in managers:
        manager.connect(pairings[manager.ranger.name])

    # 4. Connect all BLE clients and run concurrently
    print("\n✅ All paired! Connecting to robots...\n")

    async def run_one(gamepad_manager_instance: GamepadManager):
        async with gamepad_manager_instance.ranger.relay_client:
            print(f"✅ [{gamepad_manager_instance.ranger.name}] Connected!")
            await gamepad_manager_instance.run()

    async with asyncio.TaskGroup() as tg:
        for manager in managers:
            tg.create_task(run_one(manager))

    print("\n✅ All done. Goodbye!")
    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
