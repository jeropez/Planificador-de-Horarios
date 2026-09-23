"""
Cargador de datos del Planificador de Horarios.

Lee un archivo JSON (generado por `src.generador_datos`) y construye
los objetos del dominio:

    - Bloque
    - Salon
    - Profesor
    - Materia
    - Grupo
"""

import json
from pathlib import Path
from uuid import UUID

from .models.bloque import Bloque
from .models.grupo import Grupo
from .models.materia import Materia
from .models.profesor import Profesor
from .models.salon import Salon


def cargar_datos(ruta_json: str | Path) -> dict:
    """
    Carga un caso desde JSON y devuelve un dict con los objetos del dominio.

    Retorna
    -------
    dict con las llaves:
        - bloques    : list[Bloque]
        - salones    : list[Salon]
        - profesores : list[Profesor]
        - materias   : list[Materia]
        - grupos     : dict[UUID, Grupo]
    """
    
    ruta = Path(ruta_json)
    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)

    bloques: list[Bloque] = [
        Bloque(
            id=UUID(b["id"]),
            dia=b["dia"],
            hora_inicio=b["hora_inicio"],
            hora_fin=b["hora_fin"],
        )
        for b in data["calendario"]["bloques"]
    ]

    salones: list[Salon] = [
        Salon(
            id=s["id"],
            capacidad=s["capacidad"],
        )
        for s in data["salones"]
    ]

    grupos: dict[UUID, Grupo] = {
        UUID(g["id"]): Grupo(
            id=UUID(g["id"]),
            nombre=g["nombre"],
            cantidad_de_estudiantes=g["cantidad_de_estudiantes"],
            id_materia=UUID(g["id_materia"]),
        )
        for g in data["grupos"]
    }

    materias: list[Materia] = [
        Materia(
            id=UUID(m["id"]),
            nombre=m["nombre"],
            id_profesor=UUID(m["id_profesor"]),
            id_grupos=[UUID(g) for g in m["id_grupos"]],
            sesiones_semanales=m["sesiones_semanales"],
        )
        for m in data["materias"]
    ]
    
    profesores: list[Profesor] = [
        Profesor(
            id=UUID(p["id"]),
            nombre=p["nombre"],
            id_materia=UUID(p["id_materia"]),
            preferencias={
                UUID(id_bloque): valor
                for id_bloque, valor in p["preferencias"].items()
            },
        )
        for p in data["profesores"]
    ]

    return {
        "bloques": bloques,
        "salones": salones,
        "profesores": profesores,
        "materias": materias,
        "grupos": grupos,
    }