import asyncio
from bleak import BleakScanner
from rich.console import Console
from rich.table import Table


async def main():
    console = Console()

    with console.status("[bold green]Scanning for Bluetooth Low Energy devices...", spinner="dots"):
        # return_adv=True changes the return type to a dict of {address: (BLEDevice, AdvertisementData)}
        devices_dict = await BleakScanner.discover(return_adv=True)

    table = Table(title="Discovered BLE Devices", title_style="bold magenta", show_header=True,
                  header_style="bold cyan")
    table.add_column("Address / UUID", style="dim", width=40)
    table.add_column("Device Name", style="bold green")
    table.add_column("RSSI (Signal)", justify="right")

    # Iterate through the dictionary values
    for device, adv_data in devices_dict.values():
        name = device.name if device.name else "[italic red]Unknown Device[/italic red]"

        # Pull the RSSI directly from the advertisement data object
        rssi_val = adv_data.rssi

        # Color-code the signal strength
        if rssi_val > -60:
            rssi_str = f"[bold green]{rssi_val} dBm (Strong)[/bold green]"
        elif rssi_val > -80:
            rssi_str = f"[yellow]{rssi_val} dBm (Good)[/yellow]"
        else:
            rssi_str = f"[red]{rssi_val} dBm (Weak)[/red]"

        table.add_row(device.address, name, rssi_str)

    console.print("\n")
    console.print(table)
    console.print(f"[bold blue]Total devices found:[/bold blue] {len(devices_dict)}\n")


if __name__ == "__main__":
    asyncio.run(main())
