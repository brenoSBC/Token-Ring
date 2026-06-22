from packets.constants import TOKEN


def build_token() -> str:
    return str(TOKEN)


def is_token(message: str) -> bool:
    return message.strip() == str(TOKEN)
