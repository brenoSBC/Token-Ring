from dataclasses import dataclass

DATA = 2000


@dataclass
class DataPacket:
    source: str
    destination: str
    error_control: str
    CRC: int
    message: str


def build_data_packet(
    source: str,
    destination: str,
    error_control: str,
    CRC: int,
    message: str
) -> str:
    return f"{DATA}:{source}:{destination}:{error_control}:{CRC}:{message}" 

def is_data_packet(message: str) -> bool:
    return message.startswith(f"{DATA}:")

def parse_data_packet(buffer: str) -> DataPacket | None:
    parts = buffer.strip().split(":", 5)

    if len(parts) != 6:
        return None

    try:
        if int(parts[0]) != DATA:
            return None

        return DataPacket(
            source=parts[1],
            destination=parts[2],
            error_control=parts[3],
            CRC=int(parts[4]),
            message=parts[5],
        )

    except ValueError:
        return None