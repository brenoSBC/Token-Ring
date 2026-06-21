import socket
from config import FileConfig
from ring import Ring
from message_queue import MessageQueue

from packet import (
    DISCOVER,
    HELLO,
    MACHINE_NOT_FOUND,
    build_data_packet,
    build_hello,
    build_token,
    is_data_packet,
    is_token,
    parse_data_packet,
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


# recebi TOKEN
    # tenho mensagem?
        # sim -> transformo a mensagem da fila em DATA e envio para o sucessor
            # nao envio o token agora 
        # nao -> envio o TOKEN para o sucessor

# recebi DATA
    # sou a origem?
        # sim -> o pacote deu a volta 
            # removo da fila
            # libero o TOKEN
    # sou o destino?
        # sim -> mostro a mensagem
    # repasso DATA para o sucessor
def listen_unicast(cfg: FileConfig, ring: Ring, message_queue: MessageQueue):
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", cfg.port))

    print(f"Escutando unicast na porta {cfg.port}")

    while True:
        raw_data, addr = sock.recvfrom(1024)
        message = raw_data.decode()

        if is_token(message):
            print(f"\n[{cfg.letter}] Recebi TOKEN")

            successor = ring.get_next(cfg.letter)

            if successor is None:
                continue

            if message_queue.has_message():
                queued = message_queue.peek()

                packet_str = build_data_packet(origin=cfg.letter, destination=queued.destination, error_control=MACHINE_NOT_FOUND, crc=0, message=queued.message)

                print(f"[{cfg.letter}] Enviando DATA para {successor.letter}")

                send_unicast(packet_str, successor.ip, successor.port)

            else:
                print(f"[{cfg.letter}] Fila vazia. " f"Enviando TOKEN para {successor.letter}")
                send_unicast(build_token(), successor.ip, successor.port)

        # PACOTE DE DADOS
        elif is_data_packet(message):
            packet = parse_data_packet(message)

            if packet is None:
                print(f"[{cfg.letter}] Pacote DATA inválido: {message}")
                continue

            # O pacote completou uma volta no anel
            if packet.origin == cfg.letter:
                print(f"[{cfg.letter}] Meu pacote voltou. "f"Resultado: {packet.error_control}")

                message_queue.pop()

                successor = ring.get_next(cfg.letter)

                if successor is not None:
                    print(f"[{cfg.letter}] Liberando TOKEN "f"para {successor.letter}")
                    send_unicast(build_token(), successor.ip, successor.port)
                
                continue

            # Sou o destino da mensagem
            if packet.destination == cfg.letter:
                print(f"[{cfg.letter}] Mensagem recebida "f"de {packet.origin}: {packet.message}")

            # Repassa para o proximo do anel
            successor = ring.get_next(cfg.letter)

            if successor is not None:
                print(f"[{cfg.letter}] Repassando DATA "f"para {successor.letter}")

                send_unicast(message, successor.ip, successor.port)



# Cria um socket: sock = socket(AF_INET, socket.SOCK_DGRAM)
# Configura setsockopt para habilitar BROADCAST
# Escuta: bind(("", 6000))

# Entra em um loop infinito, fica esperando pacotes. Quando chega algo como: 10:A:127.0.0.1:6001
# 1. Realiza o Parse
# 2. Adiciona a máquina ao Ring
# 3. Se for DISCOVER responde HELLO
# 4. Se for HELLO não responde nada, apenas adiciona no anel
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