import sys

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
