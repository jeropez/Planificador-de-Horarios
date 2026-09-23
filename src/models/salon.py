from dataclasses import dataclass

@dataclass
class Salon:
    """
    Clase Salon que representa un salón en el sistema.
    """

    id: str
    capacidad: int
