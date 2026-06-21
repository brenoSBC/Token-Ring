from dataclasses import dataclass
from config import FileConfig


DISCOVER = 10
HELLO = 20
TOKEN = 1000
DATA = 2000
ACK = "ACK"
NAK = "NAK"
MACHINE_NOT_FOUND = "maquinainexistente"

@dataclass
class DiscoveryPacket:
    type: int
    letter: str
    ip: str
    port: int

@dataclass
class DataPacket:
    type: int
    origin: str
    destination: str
    error_control: str
    crc: int
    message: str


def build_discover(cfg: FileConfig, ip: str) -> str:
    return f"{DISCOVER}:{cfg.letter}:{ip}:{cfg.port}"


def build_hello(cfg: FileConfig, ip: str) -> str:
    return f"{HELLO}:{cfg.letter}:{ip}:{cfg.port}"

def build_data_packet(origin: str, destination: str, error_control: str, crc: int, message: str) -> str:
    return f"{DATA}:{origin}:{destination}:{error_control}:{crc}:{message}"

# Parser do pacote DISCOVERY (DiscoveryPacket)
def parse_discovery_packet(buffer: str) -> DiscoveryPacket | None:
    parts = buffer.strip().split(":")

    if len(parts) != 4:
        return None

    try:
        return DiscoveryPacket(
            type=int(parts[0]),
            letter=parts[1],
            ip=parts[2],
            port=int(parts[3]),
        )
    except ValueError:
        return None

# Parser da mensagem (DataPacket)
def parse_data_packet(buffer: str) -> DataPacket | None:
    parts = buffer.strip().split(":", maxsplit=5)

    if len(parts) != 6:
        return None

    try:
        return DataPacket(
            type=int(parts[0]),
            origin=parts[1],
            destination=parts[2],
            error_control=parts[3],
            crc=int(parts[4]),
            message=parts[5],
        )
    except ValueError:
        return None

# Verificar se o pacote é do type 2000 (mensagem, DataPacket)
def is_data_packet(message: str) -> bool:
    return message.strip().startswith(f"{DATA}:")

# Transforma o Token valor 1000 em string
def build_token() -> str:
    return str(TOKEN)


# Valida se message é o Token
def is_token(message: str) -> bool:
    return message.strip() == str(TOKEN)

