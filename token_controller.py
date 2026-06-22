from dataclasses import dataclass
import threading
from config import FileConfig
from packets.packet_token import build_token
from ring import Ring
import time



@dataclass
class TokenController:
    is_manager: bool = False
    last_token_time: float = 0.0      
    timeout: float = 0.0            
    min_interval: float = 0.0   
    remove_next_token: bool = False
    send_unicast: callable = None


    def on_token_received(self, cfg: FileConfig) -> bool:
        now = time.time()
        elapsed = now - self.last_token_time

        if self.remove_next_token:
            print(f"[{cfg.letter}] Token removido manualmente da rede.")
            self.remove_next_token = False
            self.last_token_time = now  # evita monitor reinserir imediatamente
            return False

        if self.is_manager and self.last_token_time > 0:
            if elapsed < self.min_interval:
                print(f"[{cfg.letter}] Token duplicado detectado "
                f"(chegou em {elapsed:.2f}s, mínimo é {self.min_interval}s). Descartando.")
                self.last_token_time = now
                return False

        return True
    
    def monitor_token(self, ring: Ring, cfg: FileConfig):
        while True:
            time.sleep(1)

            if self.check_token_timeout():
                print(f"[{cfg.letter}] TOKEN PERDIDO! thread {threading.current_thread().name}")
                self.insert_token(ring, cfg)

    def check_token_timeout(self) -> bool:
        # Se nunca recebeu token, não há o que verificar
        if self.last_token_time == 0:
            return False
        
        now = time.time()
        elapsed = now - self.last_token_time

        return elapsed > self.timeout

    def insert_token(self, ring: Ring, cfg: FileConfig):
        if not self.is_manager:
            print(f"[{cfg.letter}] Apenas o gerador do token pode inserir token.")
            return

        successor = ring.get_next(cfg.letter)

        if successor is None:
            print(f"[{cfg.letter}] Não há sucessor para enviar token.")
            return

        print(f"[{cfg.letter}] Inserindo TOKEN na rede -> {successor.letter}") 

        self.send_unicast(
            build_token(),
            successor.ip,
            successor.port
        )

        self.last_token_time = time.time()  # Reinicia o timer após inserir token

    def remove_token(self):
        self.remove_next_token = True
        print("Próximo token recebido será descartado.")
