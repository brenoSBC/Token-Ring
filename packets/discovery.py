from dataclasses import dataclass
from config import FileConfig
from packets.constants import DISCOVER


@dataclass(frozen=True)
class DiscoveryPacket:
    letter: str
    ip: str
    port: int


def build_discover(cfg: FileConfig, ip: str) -> str:
    return f"{DISCOVER}:{cfg.letter}:{ip}:{cfg.port}"


def is_discover(message: str) -> bool:
    return message.strip().startswith(f"{DISCOVER}:")


def parse_discover(message: str) -> DiscoveryPacket | None:
    parts = message.strip().split(":")
    if len(parts) != 4:
        return None

    try:
        packet_type = int(parts[0])
        if packet_type != DISCOVER:
            return None
        return DiscoveryPacket(letter=parts[1].upper(), ip=parts[2], port=int(parts[3]))
    except ValueError:
        return None
