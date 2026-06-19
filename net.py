import socket
from config import FileConfig
from ring import Ring
from packet import is_token, build_token
from packet import (
    DISCOVER,
    HELLO,
    build_hello,
    parse_discovery_packet,
)


BROADCAST_PORT = 6000
BROADCAST_ADDRESS = "255.255.255.255"


def send_broadcast(message: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.sendto(
        message.encode(),
        (BROADCAST_ADDRESS, BROADCAST_PORT)
    )

    sock.close()


# Envia em unicast
def send_unicast(message: str, ip: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.sendto(
        message.encode(), (ip, port))

    sock.close()


# Escuta em unicast
def listen_unicast(cfg: FileConfig, ring: Ring):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind(("", cfg.port))

    #DEBUG
    print(f"Escutando unicast na porta {cfg.port}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode()

        if is_token(message):
            #DEBUG
            print(f"\n[{cfg.letter}] Recebi TOKEN")

            successor = ring.get_next(cfg.letter)

            if successor is not None:
                #DEBUG
                print(f"[{cfg.letter}] Enviando TOKEN para {successor.letter}")
                send_unicast(build_token(), successor.ip, successor.port)


# Cria um socket: sock = socket(AF_INET, socket.SOCK_DGRAM)
# Configura setsockopt para habilitar BROADCAST
# Escuta: bind(("", 6000))

# Entra em um loop infinito, fica esperando pacotes. Quando chega algo como: 10:A:127.0.0.1:6001
# 1. Realiza o Parse
# 2. Adiciona a máquina ao Ring
# 3. Se for DISCOVER responde HELLO

def listen_broadcast(cfg: FileConfig, ring: Ring, my_ip: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("", BROADCAST_PORT))

    #DEBUG
    #print(f"Escutando broadcast na porta {BROADCAST_PORT}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode()

        packet = parse_discovery_packet(message)

        if packet is None:
            continue

        if packet.letter == cfg.letter:
            continue

        ring.add_node(packet.letter, packet.ip, packet.port)

        if packet.type == DISCOVER:
            #DEBUG
            #print(f"\nRecebi DISCOVER de {packet.letter}")

            hello = build_hello(cfg, my_ip)
            print(f"HELLO: {hello}")
            send_broadcast(hello)

        #elif packet.type == HELLO:
            #DEBUG
            #print(f"\nRecebi HELLO de {packet.letter}")

        ring.print_ring(cfg.letter)