import asyncio
import sys

import pygame


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
        if res in (0, 1): # S_OK or S_FALSE
            return
        if res == -2147417850:
            ole32.CoUninitialize()
        else:
            break

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
