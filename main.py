import sys
import time
import threading

from config import read_file
from ring import Ring
from packet import build_discover
from net import send_broadcast, listen_broadcast


MY_IP = "127.0.0.1"


def main():
    if len(sys.argv) < 2:
        print(f"Uso: python3 {sys.argv[0]} config.txt")
        return

    cfg = read_file(sys.argv[1])

    #DEBUG 
    print(f"Máquina: {cfg.letter}")
    print(f"Porta unicast: {cfg.port}")

        
    ring = Ring()                              # Cria um anel vazio
    ring.add_node(cfg.letter, MY_IP, cfg.port) # Adiciona a si mesmo no Ring

    # Cria uma nova Thread, quando ela começar, execute: listen_broadcast(cfg, ring, MY_IP)
    thread = threading.Thread(
        target=listen_broadcast,
        args=(cfg, ring, MY_IP),
        daemon=True
    )

    # Inicia a Thread criada em cima
    thread.start()

    # Dá 1 segundo para que a Thread encarregada de executar listen_broadcast consiga chegar no bind() e não perder mensagens
    time.sleep(1)

    # Construir o pacote DISCOVER no padrão do trabalho
    discover = build_discover(cfg, MY_IP)

    #DEBUG
    print(f"Enviando DISCOVER: {discover}")
    
    # Envia em broadcast o pacote DISCOVER construido
    send_broadcast(discover)

    while True:
        time.sleep(5)
        ring.print_ring(cfg.letter)


if __name__ == "__main__":
    main()