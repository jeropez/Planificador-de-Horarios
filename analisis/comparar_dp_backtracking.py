"""
Compara programación dinámica (por bloques) contra backtracking.

Parte 1: casos existentes y casos con más sesiones, ambos algoritmos.
         Se reporta la preferencia (objetivo de la DP) y la calidad completa.
Parte 2: escalabilidad, solo DP, con S creciente.

Uso (desde la raíz del proyecto):
    python -m analisis.comparar_dp_backtracking
"""
import json
import random
import tempfile
import time
from pathlib import Path

from src.backtracking import backtracking
from src.cargador import cargar_datos
from src.dinamica import dinamica, _PREF_VALOR
from src.generar_datos import generar_caso
from src.generar_sesiones import generar_sesiones
from src.indices import construir_indices


def preferencia_total(solucion, idx) -> float:
    ctx = idx["contexto_sesion"]
    return sum(
        _PREF_VALOR.get(ctx[a.id_sesion]["profesor"].preferencias.get(a.id_bloque, 1), 0.5)
        for a in solucion
    )


def caso_sintetico(materias: int, sesiones_por_materia: int, salones: int, semilla: int) -> dict:
    random.seed(semilla)
    caso = generar_caso({
        "materias": materias,
        "grupos_por_materia": 1,
        "sesiones_semanales_opciones": [sesiones_por_materia],
        "salones": salones,
        "capacidad_salon_min": 50,
        "capacidad_salon_max": 60,
        "estudiantes_min": 10,
        "estudiantes_max": 40,
    })
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "caso.json"
        ruta.write_text(json.dumps(caso), encoding="utf-8")
        return cargar_datos(ruta)


def preparar(d):
    sesiones = generar_sesiones(d["materias"], d["grupos"])
    return sesiones, construir_indices(d, sesiones)


def medir(f, *args, **kw):
    t0 = time.perf_counter()
    r = f(*args, **kw)
    return r, time.perf_counter() - t0


def main():
    print("== Parte 1: DP vs backtracking ==")
    print(f"{'caso':<14}{'S':>3} | {'DP pref':>8}{'DP cal':>8}{'DP t(s)':>10} | "
          f"{'BT pref':>8}{'BT cal':>8}{'BT t(s)':>10}{'BT nodos':>10}")
    casos = [(f"datos/{c}.json", c) for c in ["caso_pequeno", "caso_mediano", "caso_grande"]]
    datos_casos = [(n, cargar_datos(p)) for p, n in casos]
    datos_casos.append(("sint_2x2", caso_sintetico(2, 2, 2, 1)))
    for nombre, d in datos_casos:
        sesiones, idx = preparar(d)
        rd, td = medir(dinamica, sesiones, d, idx)
        rb, tb = medir(backtracking, sesiones, d, idx, buscar_optimo=True)
        pb = preferencia_total(rb["solucion"], idx)
        print(f"{nombre:<14}{len(sesiones):>3} | {rd['valor_preferencia']:>8.2f}{rd['calidad']:>8.3f}{td:>10.4f} | "
              f"{pb:>8.2f}{rb['calidad']:>8.3f}{tb:>10.4f}{rb['nodos_explorados']:>10}")

    print("\n== Parte 2: escalabilidad de la DP (solo DP) ==")
    print(f"{'S':>3}{'estados':>12}{'mascaras':>10}{'t(s)':>10}{'pref':>8}{'completa':>10}")
    for materias, por in [(3, 2), (4, 2), (5, 2), (6, 2), (7, 2)]:
        d = caso_sintetico(materias, por, 3, 10 + materias)
        sesiones, idx = preparar(d)
        r, t = medir(dinamica, sesiones, d, idx)
        print(f"{len(sesiones):>3}{r['estados_explorados']:>12}{r['mascaras_factibles']:>10}"
              f"{t:>10.3f}{r['valor_preferencia']:>8.2f}{str(r['completa']):>10}")


if __name__ == "__main__":
    main()
