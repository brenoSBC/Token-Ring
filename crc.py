import zlib


def calculate_crc32(message: str) -> int:
    return zlib.crc32(message.encode("utf-8")) & 0xFFFFFFFF
