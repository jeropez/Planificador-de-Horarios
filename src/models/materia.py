from dataclasses import dataclass
from uuid import UUID

@dataclass
class Materia:
    """
    Clase Materia que representa una materia en el sistema.
    """

    id: UUID
    nombre: str
    id_profesor: UUID
    id_grupos: list[UUID]
    sesiones_semanales: int
    