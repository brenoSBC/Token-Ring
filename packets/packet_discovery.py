from dataclasses import dataclass
from config import FileConfig

DISCOVER = 10


@dataclass
class DiscoveryPacket:
    type: int
    letter: str
    ip: str
    port: int


def build_discover(cfg: FileConfig, ip: str) -> str:
    return f"{DISCOVER}:{cfg.letter}:{ip}:{cfg.port}"

def is_discovery_packet(message: str) -> bool:
    return message.startswith(f"{DISCOVER}:")

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
