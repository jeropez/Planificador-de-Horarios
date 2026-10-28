"""
Comparativa final de las 5 técnicas (Entrega 3).

1. Mide greedy y divide y vencerás con n = 100 y n = 1000 sesiones.
2. Para fuerza bruta, backtracking y programación dinámica, que no terminan
   con esos tamaños, ESTIMA el tiempo: toma el tiempo medido en el mayor n del
   benchmark (`datos/benchmark_tecnicas.json`) y lo multiplica por lo que crece
   su fórmula de complejidad. Los cálculos se hacen en log10 porque los números
   no caben en un float.
3. Guarda `datos/comparativa_resultados.json` y la gráfica
   `docs/comparativa_tiempos.png` (tiempo vs n de las 5 técnicas).

Instancias grandes: materias de 2 sesiones (un grupo por materia), 30 bloques
y salones suficientes (S = ceil(3n / 60)): 5 salones con n = 100 y 50 con
n = 1000.

Uso (desde la raíz del proyecto):
    python -m src.comparativa              # mide n = 100 y n = 1000 (~10 min)
    python -m src.comparativa --solo-grafica   # rehace la gráfica con lo guardado
"""

import json
import math
import random
import sys
import tempfile
import time
from pathlib import Path

from .cargador import cargar_datos
from .divide_venceras import divide_venceras
from .generar_datos import generar_caso
from .generar_sesiones import generar_sesiones
from .greedy import greedy
from .indices import construir_indices

RAIZ = Path(__file__).resolve().parent.parent
TAMANOS = [100, 1000]
B = 30

NOMBRES = {
    "fuerza_bruta": "Fuerza bruta",
    "greedy": "Greedy",
    "backtracking": "Backtracking",
    "divide_venceras": "Divide y vencerás",
    "dinamica": "Programación dinámica",
}
COLORES = {
    "fuerza_bruta": "#e5484d",
    "greedy": "#e3920b",
    "backtracking": "#8e4ec6",
    "divide_venceras": "#d6409f",
    "dinamica": "#12a594",
}


def salones_para(n: int) -> int:
    return max(2, -(-n * 3 // 60))


# log10 de las operaciones según la complejidad de cada técnica (n sesiones,
# B bloques, S salones). Solo se usan para extrapolar las que no terminan.
def log_ops(tecnica: str, n: int, s: int) -> float:
    b = B * s
    if tecnica == "fuerza_bruta":            # O(n² · (B·S)^n)
        return n * math.log10(b) + 2 * math.log10(n)
    if tecnica == "backtracking":            # O((B·S)^n · n · B·S) peor caso
        return n * math.log10(b) + math.log10(n * b)
    if tecnica == "dinamica":                # O(B · 3^n)
        return math.log10(B) + n * math.log10(3)
    raise ValueError(tecnica)


def instancia(n: int) -> dict:
    random.seed(n)
    caso = generar_caso({
        "materias": n // 2, "grupos_por_materia": 1, "sesiones_semanales_opciones": [2],
        "salones": salones_para(n), "capacidad_salon_min": 50, "capacidad_salon_max": 60,
        "estudiantes_min": 10, "estudiantes_max": 40,
    })
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "caso.json"
        ruta.write_text(json.dumps(caso), encoding="utf-8")
        return cargar_datos(ruta)


def formato_tiempo(log10_s: float) -> str:
    s = 10 ** log10_s if log10_s < 300 else math.inf
    if s < 1:
        return f"{s * 1000:.1f} ms"
    if s < 60:
        return f"{s:.2f} s"
    if s < 3600:
        return f"{s / 60:.1f} min"
    if s < 86400:
        return f"{s / 3600:.1f} h"
    anios = log10_s - math.log10(3600 * 24 * 365.25)
    return f"≈10^{anios:.0f} años" if anios >= 4 else f"{10 ** anios:.0f} años"


def medir() -> dict:
    bench = json.loads((RAIZ / "datos" / "benchmark_tecnicas.json").read_text(encoding="utf-8"))
    filas = bench["resultados"]
    resultados = {}
    for n in TAMANOS:
        d = instancia(n)
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)
        s = len(d["salones"])
        for tecnica, funcion in (("greedy", greedy), ("divide_venceras", divide_venceras)):
            t0 = time.perf_counter()
            r = funcion(sesiones, d, idx)
            t = time.perf_counter() - t0
            resultados.setdefault(tecnica, {})[str(n)] = {
                "tiempo_s": t, "estimado": False, "calidad": r["calidad"], "completa": r["completa"],
            }
            print(f"n={n:<5} {NOMBRES[tecnica]:<22} {t:10.2f} s  calidad={r['calidad']:.4f}", flush=True)
        for tecnica in ("fuerza_bruta", "backtracking", "dinamica"):
            ref = max((f for f in filas if f["tecnica"] == tecnica), key=lambda f: f["S"])
            log_t = (math.log10(ref["tiempo_s"]) - log_ops(tecnica, ref["S"], bench["salones"])
                     + log_ops(tecnica, n, s))
            resultados.setdefault(tecnica, {})[str(n)] = {
                "log10_tiempo_s": log_t, "estimado": True, "texto": formato_tiempo(log_t),
            }
            print(f"n={n:<5} {NOMBRES[tecnica]:<22} {formato_tiempo(log_t):>14}  (estimado)", flush=True)
    salida = {"tamanos": TAMANOS, "salones": {str(n): salones_para(n) for n in TAMANOS}, "resultados": resultados}
    (RAIZ / "datos" / "comparativa_resultados.json").write_text(
        json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    return salida


def graficar(comp: dict) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bench = json.loads((RAIZ / "datos" / "benchmark_tecnicas.json").read_text(encoding="utf-8"))["resultados"]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
    for tecnica in NOMBRES:
        puntos = sorted((f["S"], f["tiempo_s"]) for f in bench if f["tecnica"] == tecnica)
        for n in TAMANOS:
            r = comp["resultados"][tecnica][str(n)]
            if not r["estimado"]:
                puntos.append((n, r["tiempo_s"]))
        xs, ys = zip(*puntos)
        ax.plot(xs, ys, marker="o", ms=4, lw=2, color=COLORES[tecnica], label=NOMBRES[tecnica])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n (sesiones a programar)")
    ax.set_ylabel("tiempo de ejecución (s)")
    ax.set_title("Tiempo de ejecución de las 5 técnicas (valores medidos)")
    ax.axhline(3600, color="#999", ls="--", lw=1)
    ax.text(1.05, 3600 * 1.4, "1 hora", color="#777", fontsize=8)
    ax.grid(True, which="major", alpha=.3)
    ax.legend(frameon=False, fontsize=9)
    ax.annotate("fuerza bruta y backtracking:\nsolo terminan hasta n = 4", xy=(4, 100), xytext=(6, 2000),
                fontsize=8, color="#555", arrowprops={"arrowstyle": "->", "color": "#999"})
    ax.annotate("DP: hasta n = 14\n(3^n estados)", xy=(14, 16), xytext=(25, 0.5),
                fontsize=8, color="#555", arrowprops={"arrowstyle": "->", "color": "#999"})
    fig.tight_layout()
    ruta = RAIZ / "docs" / "comparativa_tiempos.png"
    fig.savefig(ruta)
    print(f"-> {ruta.relative_to(RAIZ)}")
    return ruta


if __name__ == "__main__":
    if "--solo-grafica" in sys.argv:
        datos = json.loads((RAIZ / "datos" / "comparativa_resultados.json").read_text(encoding="utf-8"))
    else:
        datos = medir()
    graficar(datos)
