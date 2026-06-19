from dataclasses import dataclass
from threading import Lock


@dataclass
class Node:
    letter: str
    ip: str
    port: int


class Ring:
    def __init__(self):
        self.nodes: list[Node] = []
        self.lock = Lock()

    def add_node(self, letter: str, ip: str, port: int):
        with self.lock:
            for node in self.nodes:
                if node.letter == letter:
                    node.ip = ip
                    node.port = port
                    return

            self.nodes.append(Node(letter, ip, port))
            self.nodes.sort(key=lambda node: node.letter)

    def get_next(self, my_letter: str) -> Node | None:
        with self.lock:
            if not self.nodes:
                return None

            for i, node in enumerate(self.nodes):
                if node.letter == my_letter:
                    return self.nodes[(i + 1) % len(self.nodes)]

            return None

    def print_ring(self, my_letter: str):
        with self.lock:
            #text = " -> ".join(node.letter for node in self.nodes)
            #print(f"\nAnel atual: {text}")

            successor = None

            for i, node in enumerate(self.nodes):
                if node.letter == my_letter:
                    successor = self.nodes[(i + 1) % len(self.nodes)]
                    break

            #if successor:
                #print(f"Meu sucessor: {successor.letter} {successor.ip}:{successor.port}")