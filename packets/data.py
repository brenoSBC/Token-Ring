from dataclasses import dataclass, replace
from packets.constants import DATA


@dataclass(frozen=True)
class DataPacket:
    origin: str
    destination: str
    error_control: str
    crc: int
    message: str


def build_data_packet(origin: str, destination: str, error_control: str, crc: int, message: str) -> str:
    return f"{DATA}:{origin}:{destination}:{error_control}:{crc}:{message}"


def is_data_packet(message: str) -> bool:
    return message.strip().startswith(f"{DATA}:")


def parse_data_packet(buffer: str) -> DataPacket | None:
    # maxsplit=5 preserva ':' dentro da mensagem do usuário.
    parts = buffer.strip().split(":", maxsplit=5)
    if len(parts) != 6:
        return None

    try:
        packet_type = int(parts[0])
        if packet_type != DATA:
            return None
        return DataPacket(
            origin=parts[1].upper(),
            destination=parts[2].upper(),
            error_control=parts[3],
            crc=int(parts[4]),
            message=parts[5],
        )
    except ValueError:
        return None


def serialize_data_packet(packet: DataPacket) -> str:
    return build_data_packet(
        origin=packet.origin,
        destination=packet.destination,
        error_control=packet.error_control,
        crc=packet.crc,
        message=packet.message,
    )


def with_error_control(packet: DataPacket, error_control: str) -> DataPacket:
    return replace(packet, error_control=error_control)
