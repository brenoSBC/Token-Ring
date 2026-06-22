from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class Node:
    letter: str
    ip: str
    port: int


class Ring:
    def __init__(self):
        self._nodes: list[Node] = []
        self._lock = Lock()

    def size(self) -> int:
        with self._lock:
            return len(self._nodes)

    def add_node(self, letter: str, ip: str, port: int) -> None:
        letter = letter.upper()
        with self._lock:
            for index, node in enumerate(self._nodes):
                if node.letter == letter:
                    self._nodes[index] = Node(letter, ip, port)
                    self._nodes.sort(key=lambda n: n.letter)
                    return

            self._nodes.append(Node(letter, ip, port))
            self._nodes.sort(key=lambda n: n.letter)

    def has_node(self, letter: str) -> bool:
        letter = letter.upper()
        with self._lock:
            return any(node.letter == letter for node in self._nodes)

    def get_next(self, my_letter: str) -> Node | None:
        my_letter = my_letter.upper()
        with self._lock:
            if not self._nodes:
                return None

            for index, node in enumerate(self._nodes):
                if node.letter == my_letter:
                    return self._nodes[(index + 1) % len(self._nodes)]

            return None

    def first_letter(self) -> str | None:
        with self._lock:
            if not self._nodes:
                return None
            return self._nodes[0].letter

    def snapshot(self) -> list[Node]:
        with self._lock:
            return list(self._nodes)

    def as_text(self, my_letter: str | None = None) -> str:
        with self._lock:
            if not self._nodes:
                return "anel vazio"

            parts = []
            for node in self._nodes:
                label = node.letter
                if my_letter is not None and node.letter == my_letter.upper():
                    label += "(eu)"
                parts.append(label)
            return " -> ".join(parts) + f" -> {self._nodes[0].letter}"

    def print_ring(self, my_letter: str) -> None:
        successor = self.get_next(my_letter)
        successor_text = "nenhum" if successor is None else f"{successor.letter} {successor.ip}:{successor.port}"
        print(f"[ANEL] {self.as_text(my_letter)} | meu sucessor: {successor_text}")
