import socket
import time

from config import FileConfig
from crc import calculate_crc32
from fault_injector import maybe_corrupt_message
from message_queue import MessageQueue
from packets.constants import ACK, NAK, MACHINE_NOT_FOUND, BROADCAST_DESTINATION
from packets.data import (
    DataPacket,
    build_data_packet,
    is_data_packet,
    parse_data_packet,
    serialize_data_packet,
    with_error_control,
)
from packets.discovery import build_discover, is_discover, parse_discover
from packets.hello import build_hello, is_hello, parse_hello
from packets.token import build_token, is_token
from ring import Ring, Node
from state import SharedState

BROADCAST_PORT = 6000
BROADCAST_ADDRESS = "255.255.255.255"
BUFFER_SIZE = 4096


def get_local_ip() -> str:
    # Em rede real, tenta descobrir o IP da interface usada para sair
    # Se falhar, usa localhost para testes em uma máquina só
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def send_broadcast(message: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    send_message = message.encode()    
    sock.sendto(send_message, (BROADCAST_ADDRESS, BROADCAST_PORT))

    sock.close()


def send_unicast(message: str, ip: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    send_message = message.encode()
    sock.sendto(send_message, (ip, port))

    sock.close()


def send_to_successor(message: str, cfg: FileConfig, ring: Ring) -> bool:
    successor = ring.get_next(cfg.letter)
    if successor is None:
        #DEBUG
        print(f"[{cfg.letter}] Sem sucessor conhecido. Não foi possível enviar: {message}")
        return False

    time.sleep(cfg.token_time)
    send_unicast(message, successor.ip, successor.port)
    return True


def listen_broadcast(cfg: FileConfig, ring: Ring, state: SharedState, my_ip: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(("", BROADCAST_PORT))

    #DEBUG
    print(f"[{cfg.letter}] Escutando broadcast na porta {BROADCAST_PORT}")

    while state.running:

        #recv_data = bytes recebidos | addr = tupla(ip, porta)
        recv_data, addr = sock.recvfrom(BUFFER_SIZE)
        message = recv_data.decode()

        if is_discover(message):
            packet = parse_discover(message)
            if packet is None or packet.letter == cfg.letter:
                continue

            if not state.can_change_ring():
                print(f"[{cfg.letter}] DISCOVER de {packet.letter} recebido, mas há DATA em trânsito. Ignorando por enquanto.")
                continue

            ring.add_node(packet.letter, packet.ip, packet.port)
            #DEBUG
            #print(f"[{cfg.letter}] DISCOVER de {packet.letter}. Anel: {ring.as_text(cfg.letter)}")

            hello = build_hello(cfg, my_ip)
            send_broadcast(hello)
            #DEBUG
            print(f"[{cfg.letter}] HELLO: {hello}")

        elif is_hello(message):
            packet = parse_hello(message)
            if packet is None or packet.letter == cfg.letter:
                continue

            if not state.can_change_ring():
                print(f"[{cfg.letter}] HELLO de {packet.letter} recebido, mas há DATA em trânsito. Ignorando por enquanto.")
                continue

            ring.add_node(packet.letter, packet.ip, packet.port)
            #DEBUG
            #print(f"[{cfg.letter}] HELLO de {packet.letter}. Anel: {ring.as_text(cfg.letter)}")


def listen_unicast(cfg: FileConfig, ring: Ring, queue: MessageQueue, state: SharedState) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", cfg.port))
    print(f"[{cfg.letter}] Escutando unicast na porta {cfg.port}")

    while state.running:
        recv_data, addr = sock.recvfrom(BUFFER_SIZE)
        message = recv_data.decode()

        if is_token(message):
            handle_token(cfg, ring, queue, state)
        elif is_data_packet(message):
            packet = parse_data_packet(message)
            if packet is None:
                #DEBUG
                print(f"[{cfg.letter}] DATA inválido recebido: {message}")
                continue
            handle_data_packet(packet, cfg, ring, queue, state)
        else:
            #DEBUG
            print(f"[{cfg.letter}] Pacote desconhecido recebido: {message}")


def handle_token(cfg: FileConfig, ring: Ring, queue: MessageQueue, state: SharedState) -> None:
    previous_time = state.token_seen()

    # A máquina que recebeu o comando (/rt) remove o token manualmente quando receber
    if state.manually_discard_token():
        print(f"[{cfg.letter}] TOKEN removido manualmente.")
        return

    # Apenas a primeira máquina em ordem alfabética remove token duplicado
    if ring.first_letter() == cfg.letter and previous_time is not None:
        elapsed = time.time() - previous_time
        if elapsed < cfg.min_time_token:
            print(f"[{cfg.letter}] TOKEN DUPLICADO detectado ({elapsed:.2f}s < {cfg.min_time_token:.2f}s). Token extra removido.")
            return
    #DEBUG importante
    #print(f"[{cfg.letter}] TOKEN recebido")

    # Verificar a fila
    queued = queue.peek()
    if queued is None:
        successor = ring.get_next(cfg.letter)
        #DEBUG importante
        # if successor is not None:
        #     print(f"[{cfg.letter}] Fila vazia. TOKEN -> {successor.letter}")
        token_str = build_token()
        send_to_successor(token_str, cfg, ring)
        return

    state.set_data_in_transit(True)

    original_message = queued.message
    message_send = original_message
    crc_calc = calculate_crc32(original_message)

    if queued.destination != BROADCAST_DESTINATION:
        message_send, corrupted = maybe_corrupt_message(original_message, cfg.error_prob)
        if corrupted:
            print(f"[{cfg.letter}] Falha inserida artificialmente na mensagem para {queued.destination}.")

    packet = build_data_packet(origin=cfg.letter, destination=queued.destination, error_control=MACHINE_NOT_FOUND, crc=crc_calc, message=message_send)

    successor = ring.get_next(cfg.letter)
    if successor is not None:
        print(f"[{cfg.letter}] DATA -> {successor.letter} | destino={queued.destination}")
    send_to_successor(packet, cfg, ring)


def handle_data_packet(packet: DataPacket, cfg: FileConfig, ring: Ring, queue: MessageQueue, state: SharedState) -> None:
    if packet.origin == cfg.letter:
        handle_returned_data_packet(packet, cfg, ring, queue, state)
        return

    packet_to_forward = packet

    if packet.destination == cfg.letter:
        calculated_crc = calculate_crc32(packet.message)
        print(f"[{cfg.letter}] DATA recebido de {packet.origin}: {packet.message}")

        if calculated_crc == packet.crc:
            packet_to_forward = with_error_control(packet, ACK)
            print(f"[{cfg.letter}] CRC OK. Enviando ACK.")
        else:
            packet_to_forward = with_error_control(packet, NAK)
            print(f"[{cfg.letter}] CRC inválido. Enviando NAK.")

    elif packet.destination == BROADCAST_DESTINATION:
        print(f"[{cfg.letter}] BROADCAST de {packet.origin}: {packet.message}")
        # No broadcast, o controle permanece maquinainexistente e falha não é aplicada.

    successor = ring.get_next(cfg.letter)
    if successor is not None:
        print(f"[{cfg.letter}] DATA -> {successor.letter}")
    send_to_successor(serialize_data_packet(packet_to_forward), cfg, ring)


def handle_returned_data_packet(packet: DataPacket, cfg: FileConfig, ring: Ring, queue: MessageQueue, state: SharedState) -> None:
    state.set_data_in_transit(False)
    
    if packet.destination == BROADCAST_DESTINATION:
        print(f"[{cfg.letter}] Meu DATA broadcast voltou.")
    else:
        print(f"[{cfg.letter}] Meu DATA voltou. Controle={packet.error_control}")

    if packet.destination == BROADCAST_DESTINATION:
        queue.pop()
        #DEBUG
        #print(f"[{cfg.letter}] Broadcast concluído. Mensagem removida da fila.")
        release_token(cfg, ring)
        return

    if packet.error_control == ACK:
        queue.pop()
        #DEBUG
        print(f"[{cfg.letter}] ACK recebido. Mensagem entregue e removida da fila.")
        release_token(cfg, ring)
        return

    if packet.error_control == NAK:
        attempts = queue.increment_attempts()
        if attempts <= 1:
            print(f"[{cfg.letter}] NAK recebido. Mensagem será retransmitida na próxima passagem do TOKEN.")
        else:
            queue.pop()
            print(f"[{cfg.letter}] NAK recebido novamente. Mensagem descartada após uma retransmissão.")
        release_token(cfg, ring)
        return

    if packet.error_control == MACHINE_NOT_FOUND:
        queue.pop()
        print(f"[{cfg.letter}] Destino {packet.destination} não encontrado. Mensagem removida da fila.")
        release_token(cfg, ring)
        return

    queue.pop()
    print(f"[{cfg.letter}] Controle desconhecido ({packet.error_control}). Mensagem removida por segurança.")
    release_token(cfg, ring)


def release_token(cfg: FileConfig, ring: Ring) -> None:
    successor = ring.get_next(cfg.letter)
    if successor is not None:
        print(f"[{cfg.letter}] TOKEN -> {successor.letter}")
    send_to_successor(build_token(), cfg, ring)


def insert_token(cfg: FileConfig, ring: Ring, state: SharedState) -> None:
    state.token_seen()
    successor = ring.get_next(cfg.letter)
    if successor is None:
        print(f"[{cfg.letter}] Não há sucessor para inserir TOKEN.")
        return
    print(f"[{cfg.letter}] TOKEN inserido manualmente -> {successor.letter}")
    send_unicast(build_token(), successor.ip, successor.port)


def send_initial_discover(cfg: FileConfig, my_ip: str) -> None:
    discover = build_discover(cfg, my_ip)
    print(f"[{cfg.letter}] DISCOVER: {discover}")
    send_broadcast(discover)


def start_token(cfg: FileConfig, ring: Ring, state: SharedState) -> None:

    if ring.size() < 2:
        #DEBUG
        print(f"[{cfg.letter}] Apenas uma máquina no anel. TOKEN inicial não será criado ainda.")
        return
    
    if ring.first_letter() != cfg.letter:
        return

    successor = ring.get_next(cfg.letter)
    if successor is None:
        return

    state.token_seen()
    #DEBUG
    #print(f"[{cfg.letter}] Sou a primeira máquina. TOKEN inicial -> {successor.letter}")
    send_unicast(build_token(), successor.ip, successor.port)


def monitor_token(cfg: FileConfig, ring: Ring, state: SharedState) -> None:
    while state.running:
        time.sleep(0.5)

        if ring.first_letter() != cfg.letter:
            continue

        age = state.token_timelife()
        if age is None:
            continue

        if age > cfg.timeout_token:
            if state.token_removed_manually:
                print(f"[{cfg.letter}] TOKEN perdido detectado após remoção manual. Gerando novo TOKEN.")
            else:
                print(f"[{cfg.letter}] TOKEN PERDIDO detectado ({age:.2f}s > {cfg.timeout_token:.2f}s). Gerando novo TOKEN.")
            state.token_removed_manually = False
            insert_token(cfg, ring, state)
