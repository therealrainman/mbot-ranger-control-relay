from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import pygame

from src.mbot_ranger import MbotRanger

DEADZONE = 0.1
REFRESH_RATE = 0.05  # 20Hz


@dataclass
class GamepadManager:
    ranger: MbotRanger
    deadzone: float = DEADZONE
    refresh_rate: float = REFRESH_RATE
    _joystick: pygame.joystick.JoystickType | None = field(
        default=None, init=False, repr=False
    )

    def connect(self, joystick_index: int) -> None:
        self._joystick = pygame.joystick.Joystick(joystick_index)
        self._joystick.init()
        print(f"✅ Controller {joystick_index} paired to {self.ranger.name}")

    def _apply_deadzone(self, value: float) -> float:
        return 0.0 if abs(value) < self.deadzone else value

    def _compute_motor_speeds(
        self, throttle: float, steering: float
    ) -> tuple[float, float]:
        throttle = self._apply_deadzone(throttle)
        steering = self._apply_deadzone(steering)

        if throttle < 0:
            left = (throttle + steering) * 100
            right = (throttle - steering) * 100
        else:
            left = (throttle - steering) * 100
            right = (throttle + steering) * 100

        return max(-100, min(100, left)), max(-100, min(100, right))

    def _read_axes(self) -> tuple[float, float]:
        assert self._joystick is not None
        throttle = -self._joystick.get_axis(1)  # Negate: Y axis is inverted
        steering = self._joystick.get_axis(0)
        return throttle, steering

    def _handle_events(self) -> bool:
        pygame.event.pump()  # ← add this
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.JOYBUTTONDOWN and event.button == 1:
                return False
        return True

    async def run(self) -> None:
        if self._joystick is None:
            raise RuntimeError(f"Call connect() before run() for {self.ranger.name}")

        print(f"\n[{self.ranger.name}] Control layout:")
        print("  - Left Stick Y: Forward / Backward")
        print("  - Left Stick X: Left / Right (Turning)")
        print("  - Press 'B' / 'Circle' or Ctrl+C to exit")

        try:
            while self._handle_events():
                throttle, steering = self._read_axes()
                left, right = self._compute_motor_speeds(throttle, steering)
                self.ranger.set_motor_speeds_percent(left=-left, right=right)
                await self.ranger.send_to_relay()
                await asyncio.sleep(self.refresh_rate)
        except asyncio.CancelledError:
            pass
        finally:
            print(f"\n[{self.ranger.name}] Stopping...")
            self.ranger.set_motor_speeds_percent(0, 0)
            await self.ranger.send_to_relay()
