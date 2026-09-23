from dataclasses import dataclass
from uuid import UUID

@dataclass
class Profesor:
    """
    Clase Profesor que representa a un profesor en el sistema.
    """

    id: UUID
    nombre: str
    id_materia: UUID
    preferencias: dict[UUID, int]
