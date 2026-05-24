#!/usr/bin/env python3
import asyncio

import pygame

from src.game_manager import GameManager

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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping bots and shutting down...")
        pygame.quit()
