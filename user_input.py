from config import FileConfig
from message_queue import MessageQueue
from net import insert_token
from packets.constants import BROADCAST_DESTINATION
from ring import Ring
from state import SharedState


def print_menu() -> None:
    print(
        "\nComandos:\n"
        "  [/s]    <destino> <mensagem> (enviar mensagem unicast)  \n"
        "  [/bcst] <mensagem>           (enviar mensagem broadcast)\n"
        "  [/rt]                        (remover token)            \n"
        "  [/it]                        (inserir token)            \n"
        "  [/r]                         (ver o estado do anel)     \n"
        "  [/q]                         (ver o estado da fila)     \n"
        "  [/help]                      (mostrar menu)             \n"
    )


def user_input(cfg: FileConfig, ring: Ring, queue: MessageQueue, state: SharedState) -> None:
    print_menu()

    while state.running:
        try:
            line = input().strip() # input bloqueante
        except EOFError:
            state.running = False
            return

        if not line:
            continue

        if line == "/help":
            print_menu()
            continue

        if line == "/r":
            ring.print_ring(cfg.letter)
            continue

        if line == "/q":
            print(f"[{cfg.letter}] Fila: {queue.size()}/10")
            continue

        if line == "/rt":
            state.request_token_removal()
            print(f"[{cfg.letter}] O próximo TOKEN recebido será removido.")
            continue

        if line == "/it":
            insert_token(cfg, ring, state)
            continue

        if line.startswith("/bcst "):
            message = line[len("/bcst "):].strip()
            if not message:
                print("Mensagem vazia.")
                continue
            if queue.add(BROADCAST_DESTINATION, message):
                print(f"[{cfg.letter}] Broadcast adicionado na fila.")
            else:
                print(f"[{cfg.letter}] Fila cheia.")
            continue

        if line.startswith("/s "):
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                print("Uso: /s <destino> <mensagem>")
                continue
            destination = parts[1].upper()
            message = parts[2]
            if queue.add(destination, message):
                print(f"[{cfg.letter}] Mensagem para {destination} adicionada na fila.")
            else:
                print(f"[{cfg.letter}] Fila cheia.")
            continue
