"""
Genera casos con VARIAS sesiones por materia para comparar las técnicas.

En los casos originales cada materia tiene una sola sesión, así que los
términos por pares de la calidad (misma franja, mismo salón, días distintos)
no aportan y todas las técnicas empatan en calidad 1.0. Estos casos sí los
activan. No modifica caso_pequeno/mediano/grande.

Genera en `datos/`:
    - caso_multi_pequeno.json   S = 4   (todas las técnicas)
    - caso_multi_mediano.json   S = 8   (sin fuerza bruta ni backtracking)
    - caso_multi_grande.json    S = 12  (sin fuerza bruta ni backtracking)

Uso (desde la raíz del proyecto):
    python -m src.generar_casos_multisesion
"""

import random
from pathlib import Path

from .generar_datos import escribir_json, generar_caso

SEMILLA = 2026

_BASE = {
    "capacidad_salon_min": 50,
    "capacidad_salon_max": 60,
    "estudiantes_min": 10,
    "estudiantes_max": 40,
}

CONFIGURACIONES = {
    "caso_multi_pequeno": {
        **_BASE,
        "materias": 2,
        "grupos_por_materia": 1,
        "sesiones_semanales_opciones": [2],
        "salones": 2,
    },
    "caso_multi_mediano": {
        **_BASE,
        "materias": 2,
        "grupos_por_materia": 2,
        "sesiones_semanales_opciones": [2],
        "salones": 2,
    },
    "caso_multi_grande": {
        **_BASE,
        "materias": 4,
        "grupos_por_materia": 1,
        "sesiones_semanales_opciones": [3],
        "salones": 3,
    },
}


def main():
    random.seed(SEMILLA)
    carpeta_datos = Path(__file__).resolve().parent.parent / "datos"

    for nombre, config in CONFIGURACIONES.items():
        caso = generar_caso(config)
        escribir_json(carpeta_datos / f"{nombre}.json", caso)

        total_sesiones = sum(
            len(m["id_grupos"]) * m["sesiones_semanales"]
            for m in caso["materias"]
        )
        print(f"{nombre}.json generado")
        print(f"   materias : {len(caso['materias'])}")
        print(f"   grupos   : {len(caso['grupos'])}")
        print(f"   salones  : {len(caso['salones'])}")
        print(f"   sesiones : {total_sesiones}")
        print()


if __name__ == "__main__":
    main()
