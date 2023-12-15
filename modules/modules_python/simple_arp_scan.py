from scapy.all import ARP, Ether, srp1
import time
import queue

def arp_request(ip):
    # Crear una solicitud ARP para la dirección IP especificada
    arp_request = ARP(pdst=ip)

    # Crear una trama Ethernet para la solicitud ARP
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Dirección MAC de difusión

    # Combinar la trama Ethernet y la solicitud ARP
    packet = ether/arp_request

    # Enviar la solicitud ARP y esperar una respuesta
    response = srp1(packet, timeout=10, verbose=0)

    # Verificar si se recibió una respuesta y devolver la dirección MAC
    if response:
        return ip+"-"+response.hwsrc+"-Discovered by Simple Arp Scan"
    else:
        return False


# Dirección IP a verificar
target_ip = "192.168.0."  # Puedes ajustar esto según tu red

TARGET = queue.Queue()

def get_targets():
    return TARGET

def start_module():
    for i in range(20,30):
        ip = target_ip + str(i)
        # Enviar la solicitud ARP y obtener la dirección MAC o False
        mac_address = arp_request(ip)
        if mac_address != False:
            TARGET.put(mac_address)
