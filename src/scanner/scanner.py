import socket
import psutil
from scapy.layers.l2 import Ether, ARP, srp
from scan_models import Device
from scanner.scan_models import ObservedDevice


def find_subnet() -> str | None:
    interface = ""
    interfaces = psutil.net_if_addrs().keys()

    while not interface in interfaces:
        n = 0
        print("Interfaces: ")
        for i in interfaces:
            n += 1
            print(f" - {i}")

        interface = input("Choose a network interface:\n")

        if not interface in interfaces:
            print("Interface not found. Try again.")

    interface_address = psutil.net_if_addrs().get(interface)

    for i in interface_address:
        if i.family == socket.AF_INET:

            address = i.address.split(".")
            bin_address = [int(x) for x in address]

            netmask = i.netmask.split(".")
            bin_netmask = [int(x) for x in netmask]

            netmask_bit_count = 0

            for n in bin_netmask:
                netmask_bit_count += n.bit_count()

            net_address = [(bin_address[i] & bin_netmask[i]) for i in range(len(bin_address))]

            subnet_address = f"{".".join(str(i) for i in net_address)}/{netmask_bit_count}"

            return subnet_address

    return None



# def get_mac_vendor(mac_address : str) -> str | None:
#     results = requests.get(f"https://api.maclookup.app/v2/macs/{mac_address}", timeout=5)
#     results = results.json()
#
#     if not results.get("success"):
#         raise "InvalidMacRequest"
#
#     elif not results.get("found"):
#         print("MAC Vendor not found.")
#         return None
#
#     else:
#         return results.get("company")


def scanner(subnet : str | None = find_subnet()) -> list[Device] | None:
    broadcast_frame = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request = ARP(pdst=subnet)

    packet = broadcast_frame / arp_request

    answered, _ = srp(packet, timeout=2, verbose=False)

    obs_device_list = []
    if answered:
        for sent, received in answered:
            device = ObservedDevice(ip_address=received.psrc, mac_address=received.hwsrc)

#             try:
#                 device.hostname = socket.gethostbyaddr(received.psrc)[0]
#
#             except socket.herror as e:
#                 print(f"Error resolving {received.psrc}: {e.strerror} (Code: {e.errno})")
#                 pass
#
#             except socket.gaierror as e:
#                 print(f"Gaierror: Address format is invalid: {e}")
#                 pass
#
#             except OSError as e:
#                 print(f"OSError: {e}")
#                 pass

            obs_device_list.append(device)
    else:
        print("No devices found.")
        return []

    return obs_device_list