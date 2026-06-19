from dataclasses import dataclass


@dataclass
class FileConfig:
    letter: str                # Apelido (letra: A, B, C...)
    token_time: int            # Tempo do token e dos dados (seugundos)
    error_prob: int            # Probabilidade de inserir erros nas mensagens (%)
    timeout_token: float       # Timeout do token (segundos)
    min_time_token: float      # Tempo mínimo entre tokens (segundos)
    port: int                  # Porta de escuta unicast


def read_file(path: str) -> FileConfig:
    with open(path, "r") as file:
        lines = [line.strip() for line in file.readlines()]

    return FileConfig(
        letter=lines[0],
        token_time=int(lines[1]),
        error_prob=int(lines[2]),
        timeout_token=float(lines[3]),
        min_time_token=float(lines[4]),
        port=int(lines[5]),
    )