import asyncio
import sys
from dataclasses import dataclass, field

import pygame
from bleak import BleakScanner, BLEDevice
from rich.live import Live
from rich.table import Table

from src.gamepad_manager import GamepadManager
from src.mbot_ranger import MbotRanger


@dataclass
class GameManager:
    name_id_map: dict[str, str]
    scan_timeout_seconds: int = 5
    gamepad_manager_list: list[GamepadManager] = field(init=False, repr=False)

    found_devices: dict[str, BLEDevice] = field(init=False, repr=False)
    controller_pairings: dict[str, int] = field(init=False, repr=False)
    _joysticks: list[pygame.joystick.JoystickType] = field(init=False, repr=False)

    def __post_init__(self):
        self.force_mta()
        pygame.init()
        pygame.joystick.init()
        pygame.display.set_mode((1, 1))
        print("Pygame initialized!")

    @property
    def found_devices_names(self):
        return list(self.found_devices.keys())

    async def setup(self):
        # 1. Scan for all robots
        print("[ Step 1 / 3 ] Scanning for robots...")
        await self._scan_for_devices()
        self._verify_discovery()

        # 2. Verify enough controllers
        print("\n[ Step 2 / 3 ] Checking controllers...")
        self._verify_controllers()

        # 3. Interactive pairing
        print("\n[ Step 3 / 3 ] Pairing controllers to robots...")
        self._init_joysticks()
        await self._pair_controllers()

        # 4. Create GamepadManagers List
        self.gamepad_manager_list = [
            GamepadManager(
                ranger=MbotRanger(
                    name=name,
                    address=self.found_devices[name].address,
                )
            )
            for name in self.found_devices_names
        ]

        # 5. Pair controllers to GamepadManagers
        for gp_manager in self.gamepad_manager_list:
            gp_manager.connect(self.controller_pairings[gp_manager.ranger.name])

    async def run_forever(self):
        # Connect all BLE clients and run concurrently
        print("\n✅ All paired! Connecting to robots...\n")

        with Live(self._generate_table(), refresh_per_second=30) as live:
            async with asyncio.TaskGroup() as tg:
                # 1. Start robot tasks
                for gp_manager in self.gamepad_manager_list:
                    tg.create_task(self._run_single_gamepad_manager(gp_manager))

                # 2. Start table update task
                tg.create_task(self._update_dashboard(live))

    def _generate_table(self) -> Table:
        table = Table(title="mBot Ranger Dashboard")
        table.add_column("Name", justify="left", style="cyan")
        table.add_column("Address", justify="left", style="magenta")
        table.add_column("Axes", justify="left", style="yellow")
        table.add_column("Last Byte Sent", justify="left", style="bold green")

        for gp_manager in self.gamepad_manager_list:
            table.add_row(
                gp_manager.ranger.name,
                gp_manager.ranger.address,
                gp_manager.ranger.last_axes,
                gp_manager.ranger.last_payload_hex,
            )
        return table

    async def _update_dashboard(self, live: Live):
        while True:
            live.update(self._generate_table())
            await asyncio.sleep(0.033)

    ### Scan and connect to robots###
    async def _scan_for_devices(self):
        """Scan and return a map of device_name → BLEDevice for all found devices."""
        target_names = set(self.name_id_map.values())
        print(
            f"Scanning for {len(target_names)} device(s) ({self.scan_timeout_seconds}s)..."
        )
        discovered = await BleakScanner.discover(timeout=self.scan_timeout_seconds)

        found: dict[str, BLEDevice] = {}

        for device in discovered:
            if device.name in target_names:
                color = next(
                    color
                    for color, name in self.name_id_map.items()
                    if name == device.name
                )
                found[color] = device

        self.found_devices = found

    def _verify_discovery(self):
        """Print a discovery report. Returns True if all devices were found."""
        for color, device_name in self.name_id_map.items():
            if color in self.found_devices:
                print(
                    f"  ✅ {color}: {device_name} ({self.found_devices[color].address})"
                )
            else:
                print(f"  ❌ {color}: {device_name} — not found")
                print(
                    "\n❌ Not all robots were found. Please check they are powered on."
                )
                pygame.quit()
                sys.exit(1)

    def _verify_controllers(self):
        """Check that enough controllers are connected. Returns True if sufficient."""
        num_controllers_available = pygame.joystick.get_count()
        if num_controllers_available >= len(self.found_devices):
            print(
                f"  ✅ {num_controllers_available} controller(s) detected ({len(self.found_devices)} required)"
            )
        else:
            print(
                f"  ❌ {num_controllers_available} controller(s) detected, but {len(self.found_devices)} required. "
                "Please connect more controllers and try again."
            )
            sys.exit(1)

    def _init_joysticks(self):
        """Initialize all joysticks."""
        self._joysticks = [
            pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
        ]
        for j in self._joysticks:
            j.init()

    async def _pair_controllers(self):
        """
        Interactively pair each color robot to a controller.
        Returns a map of color → joystick_index, or None if pairing failed.
        """
        pygame.event.clear()  # Clear any stale events before pairing

        self.controller_pairings: dict[str, int] = {}
        used_joysticks: set[int] = set()

        for name in self.found_devices_names:
            while True:
                joystick_index = await self.wait_for_button_press(
                    button=0,  # 'A' on Xbox, 'Cross' on PS
                    prompt=f"\n🎮 Press 'A' on the controller for [{name}]...",
                )

                if joystick_index is None:
                    print(f"  ❌ Timed out waiting for [{name}]. Aborting setup.")
                    sys.exit(1)

                if joystick_index in used_joysticks:
                    print(
                        f"  ⚠️  Controller {joystick_index} is already paired. "
                        "Try a different controller."
                    )
                    continue

                used_joysticks.add(joystick_index)
                self.controller_pairings[name] = joystick_index
                print(f"  ✅ Controller {joystick_index} paired to [{name}]")
                break

    ### GamepadManager task ###
    @staticmethod
    async def _run_single_gamepad_manager(gamepad_manager_instance: GamepadManager):
        async with gamepad_manager_instance.ranger.relay_client:
            await gamepad_manager_instance.run()

    ### Helpers ###
    # noinspection PyUnresolvedReferences
    @staticmethod
    def force_mta():
        """
        Force the current thread to MTA (Multi-Threaded Apartment) mode on Windows.
        This is necessary because libraries like Pygame/SDL can initialize COM as STA,
        which breaks Bleak's WinRT callbacks.
        """
        if sys.platform != "win32":
            return
        import ctypes

        ole32 = ctypes.windll.ole32
        # COINIT_MULTITHREADED = 0x0
        # RPC_E_CHANGED_MODE = 0x80010106 (signed: -2147417850)
        # We call CoUninitialize until we can successfully set MTA or we reach a limit.
        for _ in range(10):
            res = ole32.CoInitializeEx(None, 0)
            if res in (0, 1):  # S_OK or S_FALSE
                return
            if res == -2147417850:
                ole32.CoUninitialize()
            else:
                break

    @staticmethod
    async def wait_for_button_press(
        button: int, prompt: str, timeout: float = 30.0
    ) -> int | None:
        print(prompt)
        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == button:
                    return event.joy
            await asyncio.sleep(0.05)

        return None
