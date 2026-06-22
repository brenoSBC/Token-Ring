from dataclasses import dataclass
from threading import Lock


@dataclass
class QueuedMessage:
    destination: str
    message: str
    attempts: int = 0


class MessageQueue:
    def __init__(self, max_size: int = 10):
        self._messages: list[QueuedMessage] = []
        self._max_size = max_size
        self._lock = Lock()

    def add(self, destination: str, message: str) -> bool:
        with self._lock:
            if len(self._messages) >= self._max_size:
                return False
            self._messages.append(QueuedMessage(destination.upper(), message))
            return True

    def has_message(self) -> bool:
        with self._lock:
            return bool(self._messages)

    def peek(self) -> QueuedMessage | None:
        with self._lock:
            return self._messages[0] if self._messages else None

    def pop(self) -> QueuedMessage | None:
        with self._lock:
            return self._messages.pop(0) if self._messages else None

    def increment_attempts(self) -> int:
        with self._lock:
            if not self._messages:
                return 0
            self._messages[0].attempts += 1
            return self._messages[0].attempts

    def size(self) -> int:
        with self._lock:
            return len(self._messages)
