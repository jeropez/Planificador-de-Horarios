from dataclasses import dataclass
from uuid import UUID

@dataclass
class Sesion:
    """
    Clase Sesion que representa una sesión en el sistema.
    """

    id: UUID
    id_materia: UUID
    id_grupo: UUID
