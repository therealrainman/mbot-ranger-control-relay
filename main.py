#!/usr/bin/env python3
import argparse
import asyncio

import pygame

from src.game_manager import GameManager

BUMPERBOTS_NAME_ID_MAP = {
    "Blue": "Makeblock_LE703e97e38098",
    "Red": "Makeblock_LE703e97e37282",
    "White": "Makeblock_LE10a56269e54f",
    "Yellow": "Makeblock_LE703e97e3804c",
    "Black": "Makeblock_LE10a56269e019",
    "Pink": "Makeblock_LE703e97e37fff"
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bumperbots Multi-Robot Controller Relay"
    )
    # Groundwork for additional command line flags and arguments
    return parser.parse_args()


async def main(args: argparse.Namespace):
    print("=== Bumperbots Multi-Robot Controller ===\n")

    game_manager = GameManager(BUMPERBOTS_NAME_ID_MAP)
    await game_manager.setup()
    print("Setup complete!")
    await game_manager.run_forever()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping bots and shutting down...")
        pygame.quit()
