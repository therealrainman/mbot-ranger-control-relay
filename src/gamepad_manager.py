from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable

import pygame

from rich.text import Text

from src.mbot_ranger import MbotRanger


@dataclass
class RobotDashboardRow:
    axes: Text
    payload: Text


@dataclass
class GamepadManager:
    ranger: MbotRanger
    dashboard_row: RobotDashboardRow | None = field(default=None, init=False, repr=False)
    deadzone: float = 0.1
    refresh_rate: float = 0.0333  # 30Hz
    controller_joystick: pygame.joystick.JoystickType | None = field(
        default=None, init=False, repr=False
    )
    on_update: Callable[[], None] | None = field(default=None, init=False, repr=False)

    def connect(self, joystick_index: int) -> None:
        self.controller_joystick = pygame.joystick.Joystick(joystick_index)
        if self.controller_joystick:
            self.controller_joystick.init()
        else:
            print(f"Failed to initialize controller {joystick_index} for {self.ranger}")

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
        assert self.controller_joystick is not None
        throttle = -self.controller_joystick.get_axis(1)  # Negate: Y axis is inverted
        steering = self.controller_joystick.get_axis(0)
        return throttle, steering

    async def run(self) -> None:
        if self.controller_joystick is None:
            raise RuntimeError(f"Call connect() before run() for {self.ranger.name}")

        try:
            while True:
                pygame.event.get()
                throttle, steering = self._read_axes()
                axes_str = f"T: {throttle:>5.2f} S: {steering:>5.2f}"
                self.ranger.last_axes = axes_str

                left, right = self._compute_motor_speeds(throttle, steering)
                self.ranger.set_motor_speeds_percent(left=-left, right=right)
                await self.ranger.send_to_relay()

                if self.dashboard_row:
                    self.dashboard_row.axes.plain = axes_str
                    self.dashboard_row.payload.plain = self.ranger.last_payload_hex

                if self.on_update:
                    self.on_update()
                await asyncio.sleep(self.refresh_rate)
        except asyncio.CancelledError:
            pass
        finally:
            print(f"Stopping {self.ranger}...")
            self.ranger.set_motor_speeds_percent(0, 0)
            await self.ranger.send_to_relay()
