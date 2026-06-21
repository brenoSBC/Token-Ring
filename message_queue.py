from dataclasses import dataclass
from threading import Lock


@dataclass
class QueuedMessage:
    destination: str
    message: str
    attempts: int = 0


class MessageQueue:
    def __init__(self, max_size: int = 10):
        self.messages: list[QueuedMessage] = []
        self.max_size = max_size
        self.lock = Lock()

    def add(self, destination: str, message: str) -> bool:
        with self.lock:
            if len(self.messages) >= self.max_size:
                return False

            self.messages.append(QueuedMessage(destination, message))
            return True

    def has_message(self) -> bool:
        with self.lock:
            return len(self.messages) > 0

    def peek(self) -> QueuedMessage | None:
        with self.lock:
            if not self.messages:
                return None

            return self.messages[0]

    def pop(self) -> QueuedMessage | None:
        with self.lock:
            if not self.messages:
                return None

            return self.messages.pop(0)