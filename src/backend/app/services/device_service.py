from src.backend.app.schemas.models import Device
from src.scanner.scan_models import ObservedDevice
from src.scanner.scanner import scanner
import httpx
import asyncio
import socket

async def get_mac_vendor(mac_address : str) -> str | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://api.maclookup.app/v2/macs/{mac_address}", timeout=5)

            if response.status_code != 200:
                print(f"API Error. Status code: {response.status_code}")
                return None

            data = response.json()

        except httpx.RequestError as e:
            print(f"Unable to reach API: {e}")
            return None

    if not data.get("success"):
        return None

    elif not data.get("found"):
        print("MAC Vendor not found.")
        return None
    else:
        return data.get("company")

async def get_hostname(ip: str) -> str | None:
    loop = asyncio.get_running_loop()

    try:
         result = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
         return result[0]
    except socket.herror as e:
        print(f"Error resolving {ip}: {e.strerror} (Code: {e.errno})")
        return None
    except socket.gaierror as e:
        print(f"DNS or network error while resolving {ip}: {e}")
        return None
    except OSError as e:
        print(f"OSError: {e}")
        return None

async def get_device_netdata(devices: list[ObservedDevice] | None = None) -> list[Device] | None:
    if devices is None:
        devices = scanner()

    if not devices:
        return []

    async def process_device(index, item):
        hostname_task = get_hostname(item.ip_address)
        vendor_task = get_mac_vendor(item.mac_address)

        hostname, mac_vendor = await asyncio.gather(hostname_task, vendor_task)
    
        return Device(
            id = index,
            mac_address=item.mac_address,
            ip_address=item.ip_address,
            hostname=hostname,
            mac_vendor=mac_vendor
        )

    tasks = [process_device(index, device) for index, device in enumerate(devices, start=1)]
    device_list = await asyncio.gather(*tasks) # * (unpacking)

    return device_list


