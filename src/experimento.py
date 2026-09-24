"""
Script de experimentación para medir el crecimiento de la fuerza bruta.

Corre la fuerza bruta sobre S = 1, 2, 3, 4 sesiones:

    S = 1 -> datos/exp_s1.json
    S = 2 -> datos/caso_pequeno.json
    S = 3 -> datos/caso_mediano.json
    S = 4 -> datos/caso_grande.json

Guarda resultados crudos en datos/experimento_resultados.json
y genera la gráfica en docs/complejidad_fuerza_bruta.png.

Uso (desde la raíz del proyecto):
    python -m src.experimento
"""

import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .cargador import cargar_datos
from .generar_sesiones import generar_sesiones
from .indices import construir_indices
from .fuerza_bruta import fuerza_bruta


CASOS_EXPERIMENTO = [
    ("exp_s1",        "datos/exp_s1.json"),
    ("caso_pequeno",  "datos/caso_pequeno.json"),
    ("caso_mediano",  "datos/caso_mediano.json"),
    ("caso_grande",   "datos/caso_grande.json"),
]


def correr_experimento() -> list[dict]:
    resultados = []

    for nombre, ruta in CASOS_EXPERIMENTO:
        print(f"Corriendo {nombre} ...")
        d = cargar_datos(ruta)
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)

        t0 = time.perf_counter()
        r = fuerza_bruta(sesiones, d, idx)
        t1 = time.perf_counter()

        registro = {
            "caso": nombre,
            "S": len(sesiones),
            "combinaciones_probadas": r["combinaciones_probadas"],
            "soluciones_encontradas": r["soluciones_encontradas"],
            "calidad": r["calidad"],
            "tiempo_s": t1 - t0,
        }
        resultados.append(registro)

        print(f"   S={registro['S']}  "
              f"comb={registro['combinaciones_probadas']}  "
              f"tiempo={registro['tiempo_s']:.4f}s")

    return resultados


def guardar_resultados(resultados: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"Resultados guardados en {ruta}")


def graficar(resultados: list[dict], ruta: Path) -> None:
    S_vals = [r["S"] for r in resultados]
    tiempos = [r["tiempo_s"] for r in resultados]
    combinaciones = [r["combinaciones_probadas"] for r in resultados]

    fig, ax1 = plt.subplots(figsize=(9, 6))

    # Tiempo en eje Y izquierdo (escala log)
    ax1.plot(S_vals, tiempos, "o-", color="tab:blue", label="Tiempo (s)")
    ax1.set_xlabel("Número de sesiones S")
    ax1.set_ylabel("Tiempo (s)", color="tab:blue")
    ax1.set_yscale("log")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(True, which="both", linestyle="--", alpha=0.4)
    ax1.set_xticks(S_vals)

    # Combinaciones en eje Y derecho (escala log)
    ax2 = ax1.twinx()
    ax2.plot(S_vals, combinaciones, "s--", color="tab:red",
             label="Combinaciones probadas")
    ax2.set_ylabel("Combinaciones probadas", color="tab:red")
    ax2.set_yscale("log")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title("Fuerza bruta: crecimiento con el tamaño de entrada")

    # Leyenda unificada
    lineas = ax1.get_lines() + ax2.get_lines()
    etiquetas = [l.get_label() for l in lineas]
    ax1.legend(lineas, etiquetas, loc="upper left")

    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print(f"Gráfica guardada en {ruta}")


def main():
    raiz = Path(__file__).resolve().parent.parent

    resultados = correr_experimento()

    ruta_json = raiz / "datos" / "experimento_resultados.json"
    guardar_resultados(resultados, ruta_json)

    ruta_png = raiz / "docs" / "complejidad_fuerza_bruta.png"
    graficar(resultados, ruta_png)

    print()
    print("Resumen:")
    print(f"{'S':>3} {'tiempo (s)':>14} {'comb. probadas':>20}")
    for r in resultados:
        print(f"{r['S']:>3} {r['tiempo_s']:>14.4f} {r['combinaciones_probadas']:>20}")


if __name__ == "__main__":
    main()