"""
Empaqueta los resultados para la interfaz gráfica (`interfaz/index.html`).

Lee:
    datos/<caso>.json                 (salones, grupos, profesores, materias)
    datos/salidas/<caso>/<tec>.json   (salida de src.exportar_salidas)
    datos/benchmark_tecnicas.json     (salida de analisis.benchmark_tecnicas)

Escribe `interfaz/datos.js` con `window.DATOS = {...}`. Se usa un .js y no
un .json para que la página abra con doble clic (file://) sin servidor.

Uso (desde la raíz del proyecto):
    python -m src.construir_interfaz
"""

import json
from pathlib import Path

from .exportar_salidas import CASOS, TECNICAS

RAIZ = Path(__file__).resolve().parent.parent


def _info_caso(caso: str) -> dict:
    data = json.loads((RAIZ / "datos" / f"{caso}.json").read_text(encoding="utf-8"))
    materias = {m["id"]: m for m in data["materias"]}
    return {
        "salones": [{"id": s["id"], "capacidad": s["capacidad"]} for s in data["salones"]],
        "grupos": [
            {
                "nombre": g["nombre"],
                "estudiantes": g["cantidad_de_estudiantes"],
                "materia": materias[g["id_materia"]]["nombre"],
            }
            for g in data["grupos"]
        ],
        "materias": [
            {"nombre": m["nombre"], "sesiones_semanales": m["sesiones_semanales"],
             "grupos": len(m["id_grupos"])}
            for m in data["materias"]
        ],
        "profesores": [p["nombre"] for p in data["profesores"]],
    }


def main():
    casos = []
    for caso in CASOS:
        if not (RAIZ / "datos" / f"{caso}.json").exists():
            continue
        salidas = {}
        for tecnica in TECNICAS:
            ruta = RAIZ / "datos" / "salidas" / caso / f"{tecnica}.json"
            if ruta.exists():
                s = json.loads(ruta.read_text(encoding="utf-8"))
                salidas[tecnica] = {
                    "tiempo_s": s["tiempo_s"],
                    "metricas": s["metricas"],
                    "asignaciones": s["asignaciones"],
                }
        casos.append({"id": caso, "sesiones": None, **_info_caso(caso), "salidas": salidas})
        primera = next(iter(salidas.values()), None)
        casos[-1]["sesiones"] = len(primera["asignaciones"]) if primera else 0

    ruta_bench = RAIZ / "datos" / "benchmark_tecnicas.json"
    benchmark = json.loads(ruta_bench.read_text(encoding="utf-8")) if ruta_bench.exists() else None

    destino = RAIZ / "interfaz" / "datos.js"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(
        "// Generado por `python -m src.construir_interfaz`. No editar a mano.\n"
        "window.DATOS = "
        + json.dumps({"casos": casos, "benchmark": benchmark}, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )
    print(f"{len(casos)} casos empaquetados -> {destino.relative_to(RAIZ)}")
    if benchmark is None:
        print("Aviso: falta datos/benchmark_tecnicas.json (python -m analisis.benchmark_tecnicas)")


if __name__ == "__main__":
    main()
