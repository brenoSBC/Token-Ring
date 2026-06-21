import socket
from config import FileConfig
from ring import Ring
from message_queue import MessageQueue
from packets.packet_data import DataPacket, build_data_packet, is_data_packet, parse_data_packet, MACHINE_NOT_FOUND
from packets.packet_hello import build_hello
from packets.packet_discovery import parse_discovery_packet, is_discovery_packet
from packets.packet_token import is_token, build_token


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
        handle_message(message, cfg, ring, message_queue) 
        
def handle_message(message: str, cfg: FileConfig, ring: Ring, message_queue: MessageQueue):
    if is_token(message):
        handle_token(cfg, ring, message_queue)
    elif is_data_packet(message):
        packet = parse_data_packet(message)
        if packet is None:
            print(f"[{cfg.letter}] Pacote DATA inválido: {message}")
            return
        handle_data_packet(message, packet, cfg, ring, message_queue)
    else:
        print(f"[{cfg.letter}] Mensagem desconhecida: {message}")


def handle_token(cfg: FileConfig, ring: Ring, message_queue: MessageQueue):
    print(f"\n[{cfg.letter}] Recebi TOKEN")
    successor = ring.get_next(cfg.letter)
    if successor is None:
        return

    if message_queue.has_message():
        queued = message_queue.peek()
        packet_str = build_data_packet(
            origin=cfg.letter,
            destination=queued.destination,
            error_control=MACHINE_NOT_FOUND,
            crc=0,
            message=queued.message,
        )
        print(f"[{cfg.letter}] Enviando DATA para {successor.letter}")
        send_unicast(packet_str, successor.ip, successor.port)
    else:
        print(f"[{cfg.letter}] Fila vazia. Enviando TOKEN para {successor.letter}")
        send_unicast(build_token(), successor.ip, successor.port)


def handle_data_packet(raw: str, packet: DataPacket, cfg: FileConfig, ring: Ring, message_queue: MessageQueue):
    # Pacote completou a volta
    if packet.origin == cfg.letter:
        print(f"[{cfg.letter}] Meu pacote voltou. Resultado: {packet.error_control}")
        message_queue.pop()
        _release_token(cfg, ring)
        return

    # Sou o destino
    if packet.destination == cfg.letter:
        print(f"[{cfg.letter}] Mensagem recebida de {packet.origin}: {packet.message}")
        # Aqui você ainda precisa repassar — o ACK deveria alterar o error_control
        # antes de encaminhar de volta ao anel. Deixo como ponto de atenção.

    # Repassa para o próximo (destino ou não)
    successor = ring.get_next(cfg.letter)
    if successor is not None:
        print(f"[{cfg.letter}] Repassando DATA para {successor.letter}")
        send_unicast(raw, successor.ip, successor.port)


def _release_token(cfg: FileConfig, ring: Ring):
    successor = ring.get_next(cfg.letter)
    if successor is not None:
        print(f"[{cfg.letter}] Liberando TOKEN para {successor.letter}")
        send_unicast(build_token(), successor.ip, successor.port)



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

        if is_discovery_packet(message):
            #DEBUG
            #print(f"\nRecebi DISCOVER de {packet.letter}")

            hello = build_hello(cfg, my_ip)
            print(f"HELLO: {hello}")
            send_broadcast(hello)

        #elif packet.type == HELLO:
            #DEBUG
            #print(f"\nRecebi HELLO de {packet.letter}")

        ring.print_ring(cfg.letter)