import sys
import time
import threading

from config import read_file

from ring import Ring

from packet import build_discover
from packet import build_token
from packet import build_data_packet
from packet import MACHINE_NOT_FOUND

from net import send_broadcast
from net import listen_broadcast
from net import listen_unicast
from net import send_unicast

from message_queue import MessageQueue

from user_input import user_input_loop

MY_IP = "127.0.0.1"




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

    message_queue = MessageQueue()             # Cria uma fila vazia


    # Cria uma nova Thread, quando ela começar, executa: listen_broadcast(cfg, ring, MY_IP)
    broadcast_thread = threading.Thread(
        target=listen_broadcast,
        args=(cfg, ring, MY_IP),
        daemon=True
    )

    # Cria uma nova Thread, quando ela começar, executa: listen_unicast(cfg, ring)
    unicast_thread = threading.Thread(
        target=listen_unicast,
        args=(cfg, ring, message_queue),
        daemon=True
    )

    input_thread = threading.Thread(
        target=user_input_loop,
        args=(message_queue,),
        daemon=True
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

    input_thread.start()

    if cfg.letter == "A":
        successor = ring.get_next(cfg.letter)

        if successor is not None:
            print(f"[A] Gerando TOKEN inicial para {successor.letter}")
            send_unicast(build_token(), successor.ip, successor.port)
        

    while True:
        time.sleep(5)
        #ring.print_ring(cfg.letter)


if __name__ == "__main__":
    main()