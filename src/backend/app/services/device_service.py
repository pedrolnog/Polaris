from ipaddress import IPv4Address

from src.backend.app.database.connection import update_device, get_device
from src.backend.app.schemas.models import Device
import httpx
import asyncio
import socket

async def get_mac_vendor(mac_address : str, client: httpx.AsyncClient) -> str | None:
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
        print("MAC Vendor found.")
        return data.get("company")

async def get_hostname(ip: str | IPv4Address) -> str | None:
    loop = asyncio.get_running_loop()
    ip_str = str(ip)

    try:
         result = await loop.run_in_executor(
             None,
             socket.gethostbyaddr,
             ip_str
         )
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

async def _enrich_single_device(uuid : str, client : httpx.AsyncClient, semaphore : asyncio.Semaphore) -> Device | None:
    async with semaphore: # Garante no máximo N dispositivos sendo processados simultaneamente
        try:
            device = get_device(uuid)

            hostname_task = get_hostname(device.ip_address)
            mac_task = get_mac_vendor(device.mac_address, client)

            hostname, mac_vendor = await asyncio.gather(hostname_task, mac_task)

            if hostname:
                update_device(uuid, "hostname", hostname)
            if mac_vendor:
                update_device(uuid, "mac_vendor", mac_vendor)

        except Exception as e:
            print(f"Error enriching device ({uuid}): {e}")

async def enrich_devices_task(devices_ids : list[str]) -> None:
    if not devices_ids:
        return

    # Limita a 5 dispositivos simultâneos para evitar rate limit
    semaphore = asyncio.Semaphore(5)
    async with httpx.AsyncClient() as client:
        tasks = [_enrich_single_device(uuid, client, semaphore) for uuid in devices_ids]
        await asyncio.gather(*tasks)
