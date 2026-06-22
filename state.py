import time
from threading import Lock


class SharedState:
    def __init__(self):
        self._lock = Lock()
        self.last_token_seen: float | None = None  # Guarda qual a ultima vez que viu um token
        self.discard_next_token = False            # Guarda se quando o próximo token chegar deve ser descartado (fica True quando digita /rt)
        self.token_removed_manually = False        # Guarda se o token sumiu porque o usuario removeu manualmente, serve para imprimir mensagens
        self.data_in_transit = False               # Guarda se existe um pacote circulando pelo anel
        self.running = True                        # Guarda se o programa ainda esta executando (usando em -while state.running-)

    def token_seen(self) -> float | None:
        now = time.time()
        with self._lock:
            previous = self.last_token_seen
            self.last_token_seen = now
            return previous

    def manually_discard_token(self) -> bool:
        with self._lock:
            if not self.discard_next_token:
                return False
            self.discard_next_token = False
            self.token_removed_manually = True
            return True

    def request_token_removal(self) -> None:
        with self._lock:
            self.discard_next_token = True

    def set_data_in_transit(self, value: bool) -> None:
        with self._lock:
            self.data_in_transit = value

    def can_change_ring(self) -> bool:
        with self._lock:
            return not self.data_in_transit

    def token_timelife(self) -> float | None:
        with self._lock:
            if self.last_token_seen is None:
                return None
            return time.time() - self.last_token_seen
