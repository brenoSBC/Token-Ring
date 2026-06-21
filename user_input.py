from message_queue import MessageQueue


def user_input_loop(message_queue: MessageQueue):
    while True:
        destination = input("Destino: ").strip()
        message = input("Mensagem: ").strip()

        if not destination or not message:
            print("Destino e mensagem não podem ser vazios.")
            continue

        if message_queue.add(destination, message):
            print(f"Mensagem para {destination} adicionada na fila.")
        else:
            print("Fila cheia.")