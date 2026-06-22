import sys
import argparse
import threading
import time

from config import read_file
from message_queue import MessageQueue
from net import (
    get_local_ip,
    listen_broadcast,
    listen_unicast,
    monitor_token,
    send_initial_discover,
    start_token,
)
from ring import Ring
from state import SharedState
from user_input import user_input

def main() -> None:
    
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} config.txt [--localhost]")
        return
    
    config_path = sys.argv[1]
    use_localhost = "--localhost" in sys.argv

    cfg = read_file(config_path)
    my_ip = "127.0.0.1" if use_localhost else get_local_ip()

    ring = Ring()
    ring.add_node(cfg.letter, my_ip, cfg.port)

    queue = MessageQueue(max_size=10)
    state = SharedState()

    print(f"[{cfg.letter}] IP anunciado: {my_ip}")
    print(f"[{cfg.letter}] Porta unicast: {cfg.port}")

    broadcast_thread = threading.Thread(target=listen_broadcast, args=(cfg, ring, state, my_ip), daemon=True)
    unicast_thread   = threading.Thread(target=listen_unicast, args=(cfg, ring, queue, state), daemon=True)
    token_thread     = threading.Thread(target=monitor_token, args=(cfg, ring, state), daemon=True)
    user_thread      = threading.Thread(target=user_input, args=(cfg, ring, queue, state), daemon=True)
        
    broadcast_thread.start()
    unicast_thread.start()
    token_thread.start()
    user_thread.start()

    # Sleep para garantir que as Threads com socket cheguem no bind antes do primeiro broadcast
    time.sleep(1)
    send_initial_discover(cfg, my_ip)

    # Janela simples de descoberta inicial.
    time.sleep(3)
    ring.print_ring(cfg.letter)
    start_token(cfg, ring, state)

    try:
        while state.running:
            time.sleep(1)
    except KeyboardInterrupt:
        state.running = False
        print(f"\n[{cfg.letter}] Encerrando.")


if __name__ == "__main__":
    main()
