from dataclasses import dataclass


@dataclass(frozen=True)
class FileConfig:
    letter: str
    token_time: float
    error_prob: int
    timeout_token: float
    min_time_token: float
    port: int


def read_file(path: str) -> FileConfig:
    with open(path, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    if len(lines) < 6:
        raise ValueError("Arquivo de configuração deve ter 6 linhas não vazias")

    return FileConfig(
        letter=lines[0].upper(),
        token_time=float(lines[1]),
        error_prob=int(lines[2]),
        timeout_token=float(lines[3]),
        min_time_token=float(lines[4]),
        port=int(lines[5]),
    )
