import asyncio
import pygame

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
