from scapy.all import ARP, Ether, srp1
import time
import queue
import ipaddress

class  net_ip:
    def __init__(self,ip, netmask):
        self.ip = ip.split(".")
        self.netmask = netmask.split(".")
        self.broadcast = self.get_broadcast()

    def get_broadcast(self):
        try:
            net = ipaddress.IPv4Network(f"{self.get_ip()}/{self.get_netmask()}",strict=False)

            broadcast_address = str(net.broadcast_address)
            return broadcast_address
        except ValueError as e:
            return e

    def get_ip(self):
        return str(self.ip[0]+"."+self.ip[1]+"."+self.ip[2]+"."+self.ip[3])

    def get_netmask(self):
        return str(self.netmask[0]+"."+self.netmask[1]+"."+self.netmask[2]+"."+self.netmask[3])

    def plus(self):
        self.ip[3] = str(int(self.ip[3]) + 1)

        if self.ip[3] == "256" and self.get_ip() != self.broadcast:
            self.ip[3] = "0"
            self.ip[2] = str(int(self.ip[2])+1)
            if self.ip[2] == "256" and self.get_ip() != self.broadcast:
                self.ip[2] = "0"
                self.ip[1] = str(int(self.ip[1])+1)
                if self.ip[1] == "256" and self.get_ip() != self.broadcast:
                    self.ip[1] = "0"
                    self.ip[0] = str(int(self.ip[0])+1)
                    if self.ip[0] == "256" and self.get_ip() != self.broadcast:
                        self.ip[0] = "0"
                        return False
        elif self.get_ip() == self.broadcast:
            return False

        return True


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

TARGET = queue.Queue()

def get_targets():
    return TARGET

def start_module(net, netmask, interface):

    ip = net_ip(net,netmask)
    mac_address = arp_request(ip.get_ip())
    if mac_address != False:
        TARGET.put(mac_address)
    while ip.plus():
        mac_address = arp_request(ip.get_ip())
        if mac_address != False:
            TARGET.put(mac_address)
'''
    for i in range(1,255):
        ip = target_ip + str(i)
        # Enviar la solicitud ARP y obtener la dirección MAC o False
        mac_address = arp_request(ip)
        if mac_address != False:
            TARGET.put(mac_address)
'''
