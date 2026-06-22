import sys
import time
import threading

from config import read_file
from ring import Ring
from packets.packet_discovery import build_discover
from packets.packet_token import build_token
from net import send_broadcast, listen_broadcast, listen_unicast, send_unicast
from message_queue import MessageQueue
from token_controller import TokenController


MY_IP = "127.0.0.1"

def print_menu():
    print("\n" + "="*35)
    print("  [r] Retirar token da rede")
    print("  [i] Inserir token na rede")
    print("  [s] Status do anel")
    print("  [q] Sair")
    print("="*35)
    print("> ", end="", flush=True)

def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} config.txt")
        return

    cfg = read_file(sys.argv[1])

    #DEBUG 
    #print(f"Máquina: {cfg.letter}")
    #print(f"Porta unicast: {cfg.port}")

        
    ring = Ring()                              # Cria um anel vazio
    ring.add_node(cfg.letter, MY_IP, cfg.port) # Adiciona a si mesmo no Ring

    message_queue = MessageQueue() # Cria uma fila de mensagens

    token_controller = TokenController(
        is_manager=(cfg.letter == "A"),
        timeout=cfg.timeout_token,
        min_interval=cfg.min_time_token,
        send_unicast=send_unicast
    )

    # Cria uma nova Thread, quando ela começar, executa: listen_broadcast(cfg, ring, MY_IP)
    broadcast_thread = threading.Thread(
        target=listen_broadcast,
        args=(cfg, ring, MY_IP),
        daemon=True,
        name="BroadcastThread"
    )

    # Cria uma nova Thread, quando ela começar, executa: listen_unicast(cfg, ring)
    unicast_thread = threading.Thread(
        target=listen_unicast,
        args=(cfg, ring, message_queue, token_controller),
        daemon=True,
        name="UnicastThread"
    )

    broadcast_thread.start() # Inicia a Thread de broadcast
    unicast_thread.start()   # Inicia a Thread de unicast

    # Dá 1 segundo para que a Thread encarregada de executar listen_broadcast consiga chegar no bind() e não perder mensagens
    time.sleep(1)

    # Construir o pacote DISCOVER no padrão do trabalho
    discover = build_discover(cfg, MY_IP)

    #DEBUG
    print(f"DISCOVER: {discover}")
    
    # Envia em broadcast o pacote DISCOVER construido
    send_broadcast(discover)

    # Sleep para garantir que todos os DISCOVER e HELLO aconteceram (seria melhor usar um contador, mas enfim...tanto faz)
    time.sleep(3)

    if token_controller.is_manager:
        token_controller.insert_token(ring, cfg)
        
        monitor_thread = threading.Thread(
            target=token_controller.monitor_token,
            args=(ring, cfg),
            daemon=True,
            name="MonitorThread"
        )

        monitor_thread.start()
        

    while True:
        print_menu()
        try:
            cmd = input().strip().lower()
        except EOFError:
            break

        if cmd == 'r':
            token_controller.remove_token()

        elif cmd == 'i':
            if token_controller.is_manager:
                token_controller.insert_token(ring, cfg)
            else:
                print(f"[{cfg.letter}] Apenas o gerenciador do token pode inserir.")

        elif cmd == 's':
            ring.print_ring(cfg.letter)

        elif cmd == 'q':
            print("Encerrando...")
            break


if __name__ == "__main__":
    main()