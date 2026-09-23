from dataclasses import dataclass
from uuid import UUID

@dataclass
class Grupo:
    """
    Clase Grupo que representa un grupo en el sistema.
    """

    id: UUID
    nombre: str
    cantidad_de_estudiantes: int
    id_materia: UUID
    