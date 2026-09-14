from enum import Enum


class Suspeita(Enum):
    AUTISMO = "Autismo"
    TDAH = "TDAH"

    def __str__(self) -> str:
        return self.value
