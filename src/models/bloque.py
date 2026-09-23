from dataclasses import dataclass
from uuid import UUID

@dataclass
class Bloque:
    """
    Clase Bloque que representa un bloque de tiempo en el sistema.
    """

    id: UUID
    dia: str
    hora_inicio: str
    hora_fin: str
