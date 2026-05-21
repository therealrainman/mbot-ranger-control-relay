# mbot-ranger-control-relay
Control relay for the Makeblock mBot Ranger

## Running the Demo

1. Turn on the mBot Ranger and place it close to the computer.
2. Turn on the computer's Bluetooth.
   > **Note:** The mBot Ranger uses BLE (Bluetooth Low Energy) and will not appear as a normal
   > device under Bluetooth settings. This is normal.
3. Ensure the terminal/text editor/IDE running Python has system-level permissions to access Bluetooth.
4. Run `main.py`. For faster setup, install [uv](https://docs.astral.sh/uv/) and run:
   ```bash
   uv run main.py
   ```
