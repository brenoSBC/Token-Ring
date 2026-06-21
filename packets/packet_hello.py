from dataclasses import dataclass

HELLO = 20


@dataclass
class HelloPacket:
    letter: str
    ip: str
    port: int


def build_hello(letter: str, ip: str, port: int) -> str:
    return f"{HELLO}:{letter}:{ip}:{port}"

def is_hello(message: str) -> bool:
    return message.startswith(f"{HELLO}:")

def parse_hello(buffer: str) -> HelloPacket | None:
    parts = buffer.strip().split(":")

    if len(parts) != 4:
        return None

    try:
        if int(parts[0]) != HELLO:
            return None

        return HelloPacket(
            letter=parts[1],
            ip=parts[2],
            port=int(parts[3]),
        )

    except ValueError:
        return None