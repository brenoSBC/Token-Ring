import random


def maybe_corrupt_message(message: str, probability_percent: int) -> tuple[str, bool]:
    if not message:
        return message, False

    probability = max(0, min(100, probability_percent))
    if random.randint(1, 100) > probability:
        return message, False

    index = random.randrange(len(message))
    original = message[index]
    replacement = chr((ord(original) + 1) % 127)
    if replacement == "\x00" or replacement == ":":
        replacement = "?"

    corrupted = message[:index] + replacement + message[index + 1:]
    return corrupted, True
