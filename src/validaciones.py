"""
Validadores de restricciones duras del Planificador de Horarios.

Todas las funciones son puras: no modifican el estado, solo responden
si una asignación propuesta es válida según las restricciones R1–R5.

R1 — Capacidad del salón
R2 — Disponibilidad del salón (cubierta por R3: si el salón está libre,
     está disponible)
R3 — Un salón no puede tener dos clases simultáneamente
R4 — Un profesor no puede impartir dos clases simultáneamente
R5 — Un grupo no puede recibir dos clases simultáneamente
"""

from .models.asignacion import Asignacion
from .models.bloque import Bloque
from .models.grupo import Grupo
from .models.salon import Salon


def cumple_r1_capacidad(salon: Salon, grupo: Grupo) -> bool:
    """R1: el salón debe tener capacidad suficiente para el grupo."""
    return salon.capacidad >= grupo.cantidad_de_estudiantes


def hay_conflicto_salon(
    asignaciones: list[Asignacion],
    id_salon: str,
    id_bloque,
) -> bool:
    """R3: un salón no puede tener dos clases en el mismo bloque."""
    return any(
        a.id_salon == id_salon and a.id_bloque == id_bloque
        for a in asignaciones
    )


def hay_conflicto_profesor(
    asignaciones: list[Asignacion],
    contexto_sesion: dict,
    id_profesor,
    id_bloque,
) -> bool:
    """R4: un profesor no puede impartir dos clases en el mismo bloque."""
    for a in asignaciones:
        ctx = contexto_sesion[a.id_sesion]
        if ctx["profesor"].id == id_profesor and a.id_bloque == id_bloque:
            return True
    return False


def hay_conflicto_grupo(
    asignaciones: list[Asignacion],
    contexto_sesion: dict,
    id_grupo,
    id_bloque,
) -> bool:
    """R5: un grupo no puede recibir dos clases en el mismo bloque."""
    for a in asignaciones:
        ctx = contexto_sesion[a.id_sesion]
        if ctx["grupo"].id == id_grupo and a.id_bloque == id_bloque:
            return True
    return False