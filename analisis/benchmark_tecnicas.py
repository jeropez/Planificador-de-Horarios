"""
Mide tiempo, calidad y trabajo de cada técnica para S = 1 .. 14 sesiones.

Las instancias se generan con `generar_caso` (2 salones, materias de 2
sesiones; si S es impar la última materia tiene 1). Fuerza bruta y
backtracking solo se corren hasta S = 4: por encima tardan horas.

Escribe `datos/benchmark_tecnicas.json`, que usa la interfaz gráfica.

Uso (desde la raíz del proyecto):
    python -m analisis.benchmark_tecnicas                    # todas las técnicas
    python -m analisis.benchmark_tecnicas divide_venceras    # solo esas; actualiza
                                                             # sus filas en el JSON
Advertencia: con todas tarda ~5 minutos (casi todo es S = 4 en fuerza bruta).
"""
import json
import random
import sys
import tempfile
import time
from pathlib import Path

from src.backtracking import backtracking
from src.cargador import cargar_datos
from src.dinamica import _PREF_VALOR, dinamica
from src.divide_venceras import divide_venceras
from src.fuerza_bruta import fuerza_bruta
from src.generar_datos import generar_caso
from src.generar_sesiones import generar_sesiones
from src.greedy import greedy
from src.indices import construir_indices

S_MAX = 14
MAX_EXHAUSTIVO = 4
SEMILLA = 7

TECNICAS = {
    "fuerza_bruta": (fuerza_bruta, "combinaciones_probadas"),
    "greedy": (greedy, "candidatos_evaluados"),
    "backtracking": (backtracking, "nodos_explorados"),
    "dinamica": (dinamica, "estados_explorados"),
    "divide_venceras": (divide_venceras, "combinaciones_evaluadas"),
}


def instancia(s: int) -> dict:
    random.seed(SEMILLA + s)
    caso = generar_caso({
        "materias": (s + 1) // 2,
        "grupos_por_materia": 1,
        "sesiones_semanales_opciones": [2],
        "salones": 2,
        "capacidad_salon_min": 50,
        "capacidad_salon_max": 60,
        "estudiantes_min": 10,
        "estudiantes_max": 40,
    })
    if s % 2:
        caso["materias"][-1]["sesiones_semanales"] = 1
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "caso.json"
        ruta.write_text(json.dumps(caso), encoding="utf-8")
        return cargar_datos(ruta)


def preferencia(solucion, idx) -> float:
    ctx = idx["contexto_sesion"]
    return sum(
        _PREF_VALOR.get(ctx[a.id_sesion]["profesor"].preferencias.get(a.id_bloque, 1), 0.5)
        for a in solucion or []
    )


def main(elegidas: list[str] | None = None):
    salida = Path(__file__).resolve().parent.parent / "datos" / "benchmark_tecnicas.json"
    resultados = []
    if elegidas and salida.exists():
        # Se conservan las filas de las técnicas que no se vuelven a medir.
        previos = json.loads(salida.read_text(encoding="utf-8"))["resultados"]
        resultados = [r for r in previos if r["tecnica"] not in elegidas]
    for s in range(1, S_MAX + 1):
        d = instancia(s)
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)
        for nombre, (funcion, contador) in TECNICAS.items():
            if elegidas and nombre not in elegidas:
                continue
            if nombre in ("fuerza_bruta", "backtracking") and s > MAX_EXHAUSTIVO:
                continue
            t0 = time.perf_counter()
            r = funcion(sesiones, d, idx)
            t = time.perf_counter() - t0
            fila = {
                "S": len(sesiones),
                "tecnica": nombre,
                "tiempo_s": t,
                "calidad": r["calidad"],
                "preferencia": preferencia(r["solucion"], idx),
                "trabajo": r[contador],
                "completa": bool(r["solucion"]) and len(r["solucion"]) == len(sesiones),
            }
            resultados.append(fila)
            print(f"S={fila['S']:>2} {nombre:<15} t={t:>10.4f}s  calidad={r['calidad']:.3f}  "
                  f"trabajo={r[contador]}", flush=True)

    resultados.sort(key=lambda r: (r["S"], list(TECNICAS).index(r["tecnica"])))
    salida.write_text(json.dumps({
        "descripcion": "2 salones, 30 bloques, materias de 2 sesiones; S = sesiones",
        "bloques": 30,
        "salones": 2,
        "resultados": resultados,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> {salida}")


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if a in TECNICAS] or None)
