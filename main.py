#!/usr/bin/env python3
from __future__ import annotations
from src.game_manager import GameManager
import asyncio
import pygame

BUMPERBOTS_NAME_ID_MAP = {
    "Blue": "Makeblock_LE703e97e38098",
    "Red": "Makeblock_LE10a56269e063",
    # "Green": "Makeblock_LE003",
    # "Yellow": "Makeblock_LE004",
}

async def main():
    print("=== Bumperbots Multi-Robot Controller ===\n")

    game_manager = GameManager(BUMPERBOTS_NAME_ID_MAP)
    await game_manager.setup()
    print("Setup complete!")
    await game_manager.run_forever()

    print("\n✅ All done. Goodbye!")
    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
