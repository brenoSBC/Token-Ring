from dataclasses import dataclass
from config import FileConfig
from packets.constants import HELLO


@dataclass(frozen=True)
class HelloPacket:
    letter: str
    ip: str
    port: int


def build_hello(cfg: FileConfig, ip: str) -> str:
    return f"{HELLO}:{cfg.letter}:{ip}:{cfg.port}"


def is_hello(message: str) -> bool:
    return message.strip().startswith(f"{HELLO}:")


def parse_hello(message: str) -> HelloPacket | None:
    parts = message.strip().split(":")
    if len(parts) != 4:
        return None

    try:
        packet_type = int(parts[0])
        if packet_type != HELLO:
            return None
        return HelloPacket(letter=parts[1].upper(), ip=parts[2], port=int(parts[3]))
    except ValueError:
        return None
