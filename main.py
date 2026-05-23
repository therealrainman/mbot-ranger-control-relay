#!/usr/bin/env python3
from __future__ import annotations

import sys

from src.game_manager import GameManager
from src.utils import force_mta

# Set coinit_flags before any COM-related imports to ensure MTA on Windows
sys.coinit_flags = 0  # 0 means MTA (for pythoncom)

# Attempt to force MTA before importing other modules
force_mta()

import asyncio

import pygame

# Use bleak's allow_sta as a fallback. If forcing MTA fails, allow_sta()
# tells Bleak to trust that we are running a message loop.
if sys.platform == "win32":
    try:
        from bleak.backends.winrt.util import allow_sta
        allow_sta()
    except (ImportError, AttributeError):
        pass

BUMPERBOTS_NAME_ID_MAP = {
    "Blue": "Makeblock_LE703e97e38098",
    "Red": "Makeblock_LE10a56269e063",
    # "Green": "Makeblock_LE003",
    # "Yellow": "Makeblock_LE004",
}

async def main():
    print("=== Bumperbots Multi-Robot Controller ===\n")

    pygame.init()
    pygame.joystick.init()

    # Re-force MTA on Windows after pygame initialization
    force_mta()

    await GameManager(BUMPERBOTS_NAME_ID_MAP).run_forever()
    print("\n✅ All done. Goodbye!")
    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
