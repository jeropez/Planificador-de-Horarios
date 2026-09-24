"""
Genera el caso experimental con S = 1 sesión.

Produce: datos/exp_s1.json
No modifica los casos caso_pequeno / caso_mediano / caso_grande.
"""

import json
import random
from pathlib import Path
from uuid import uuid4

from .generar_datos import (
    DIAS,
    FRANJAS,
    SEMILLA,
    NOMBRES_MATERIAS,
)


def generar_exp_s1():
    random.seed(SEMILLA)

    bloques = []
    for dia in DIAS:
        for hora_inicio, hora_fin in FRANJAS:
            bloques.append({
                "id": str(uuid4()),
                "dia": dia,
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin,
            })

    # 2 salones con capacidad sobrada
    salones = [
        {"id": "1-101", "capacidad": 60},
        {"id": "2-201", "capacidad": 60},
    ]

    id_materia = uuid4()

    grupo = {
        "id": str(uuid4()),
        "nombre": "G01",
        "cantidad_de_estudiantes": 30,
        "id_materia": str(id_materia),
    }

    profesor = {
        "id": str(uuid4()),
        "nombre": "Profesor_01",
        "id_materia": str(id_materia),
        "preferencias": {
            b["id"]: random.choice([0, 1, 2])
            for b in bloques
        },
    }

    materia = {
        "id": str(id_materia),
        "nombre": NOMBRES_MATERIAS[0],
        "id_profesor": profesor["id"],
        "id_grupos": [grupo["id"]],
        "sesiones_semanales": 1,
    }

    return {
        "calendario": {"bloques": bloques},
        "salones": salones,
        "profesores": [profesor],
        "materias": [materia],
        "grupos": [grupo],
    }


def main():
    raiz = Path(__file__).resolve().parent.parent
    ruta = raiz / "datos" / "exp_s1.json"

    caso = generar_exp_s1()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(caso, f, indent=2, ensure_ascii=False)

    print(f"exp_s1.json generado en {ruta}")
    print(f"   sesiones: 1")


if __name__ == "__main__":
    main()