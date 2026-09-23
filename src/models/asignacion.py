from dataclasses import dataclass
from uuid import UUID

@dataclass
class Asignacion:
    """
    Clase Asignacion que representa una asignación en el sistema.
    """

    id_sesion: UUID
    id_salon: str
    id_bloque: UUID