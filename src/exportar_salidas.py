"""
Exporta el horario generado por cada técnica a JSON.

Para cada caso de `datos/` corre fuerza bruta, greedy, backtracking y
programación dinámica, y escribe:

    datos/salidas/<caso>/<tecnica>.json

Cada archivo contiene las métricas de la corrida, la lista de asignaciones
legible (materia, profesor, grupo, día, franja, salón) y el horario por salón
en el mismo formato de `salida.formatear_horario`.

Uso (desde la raíz del proyecto):
    python -m src.exportar_salidas                          # todos los casos
    python -m src.exportar_salidas caso_multi_grande        # solo los indicados
    python -m src.exportar_salidas --sin-fuerza-bruta       # omite la más lenta

Fuerza bruta y backtracking se omiten cuando S > 4 (ver MAX_SESIONES).
Advertencia: con S = 4 la fuerza bruta tarda ~2 min y backtracking ~1 min.
"""

import json
import sys
import time
from pathlib import Path

from .backtracking import backtracking
from .cargador import cargar_datos
from .dinamica import dinamica
from .fuerza_bruta import fuerza_bruta
from .generar_sesiones import generar_sesiones
from .greedy import greedy
from .indices import construir_indices
from .salida import DIAS, formatear_horario

CASOS = [
    "caso_pequeno", "caso_mediano", "caso_grande",
    "caso_multi_pequeno", "caso_multi_mediano", "caso_multi_grande",
]

# Máximo de sesiones con el que cada técnica exhaustiva termina en minutos.
# Por encima se omite (fuerza bruta crece como 60^S y backtracking recorre
# todo el árbol buscando el óptimo).
MAX_SESIONES = {
    "fuerza_bruta": 4,
    "backtracking": 4,
}

TECNICAS = {
    "fuerza_bruta": fuerza_bruta,
    "greedy": greedy,
    "backtracking": backtracking,
    "dinamica": dinamica,
}


def _asignaciones_legibles(solucion, datos, indices) -> list[dict]:
    """Lista ordenada por día y franja, una entrada por sesión asignada."""
    contexto = indices["contexto_sesion"]
    bloques_por_id = {b.id: b for b in datos["bloques"]}
    filas = []
    for a in solucion:
        ctx = contexto[a.id_sesion]
        b = bloques_por_id[a.id_bloque]
        filas.append({
            "materia": ctx["materia"].nombre,
            "profesor": ctx["profesor"].nombre,
            "grupo": ctx["grupo"].nombre,
            "dia": b.dia,
            "franja": f"{b.hora_inicio}-{b.hora_fin}",
            "salon": a.id_salon,
            "preferencia_profesor": ctx["profesor"].preferencias.get(a.id_bloque, 1),
        })
    filas.sort(key=lambda f: (DIAS.index(f["dia"]), f["franja"], f["salon"]))
    return filas


def _metricas(resultado: dict) -> dict:
    """Copia las métricas numéricas/booleanas que devuelve cada técnica."""
    return {
        k: v for k, v in resultado.items()
        if isinstance(v, (int, float, bool))
    }


def exportar(casos: list[str], incluir_fuerza_bruta: bool = True) -> None:
    raiz = Path(__file__).resolve().parent.parent
    carpeta = raiz / "datos" / "salidas"

    for caso in casos:
        d = cargar_datos(raiz / "datos" / f"{caso}.json")
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)

        for nombre, funcion in TECNICAS.items():
            if nombre == "fuerza_bruta" and not incluir_fuerza_bruta:
                continue
            if len(sesiones) > MAX_SESIONES.get(nombre, len(sesiones)):
                print(f"{caso:<19} {nombre:<13} omitido (S={len(sesiones)} > "
                      f"{MAX_SESIONES[nombre]})", flush=True)
                continue

            t0 = time.perf_counter()
            r = funcion(sesiones, d, idx)
            t = time.perf_counter() - t0

            solucion = r["solucion"] or []
            contenido = {
                "caso": caso,
                "tecnica": nombre,
                "sesiones": len(sesiones),
                "tiempo_s": round(t, 6),
                "metricas": _metricas(r),
                "asignaciones": _asignaciones_legibles(solucion, d, idx),
                "horario_por_salon": formatear_horario(solucion, d, idx),
            }

            ruta = carpeta / caso / f"{nombre}.json"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(contenido, f, indent=2, ensure_ascii=False)

            print(f"{caso:<19} {nombre:<13} calidad={r['calidad']:.4f}  "
                  f"tiempo={t:.4f}s  -> {ruta.relative_to(raiz)}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    elegidos = [a for a in args if not a.startswith("--")] or CASOS
    exportar(elegidos, incluir_fuerza_bruta="--sin-fuerza-bruta" not in args)
