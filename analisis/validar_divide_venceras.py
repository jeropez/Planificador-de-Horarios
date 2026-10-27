"""
Valida divide y vencerás contra un óptimo exhaustivo en instancias pequeñas.

Usa el mismo generador y el mismo óptimo exhaustivo que
`contraejemplo_greedy.py`. Para cada instancia con solución completa revisa:
  - que la solución cumpla R1, R3, R4 y R5,
  - si su calidad iguala al óptimo, y
  - que nunca marque `optimo_garantizado` cuando no lo es.

Uso (desde la raíz del proyecto):
    python -m analisis.validar_divide_venceras
"""
import random
import sys

sys.path.insert(0, ".")

from analisis.contraejemplo_greedy import generar, optimo
from src.divide_venceras import divide_venceras
from src.generar_sesiones import generar_sesiones
from src.indices import construir_indices


def es_valida(solucion, datos, indices) -> bool:
    ctx = indices["contexto_sesion"]
    capacidad = {s.id: s.capacidad for s in datos["salones"]}
    vistos = set()
    for a in solucion:
        c = ctx[a.id_sesion]
        if capacidad[a.id_salon] < c["grupo"].cantidad_de_estudiantes:          # R1
            return False
        for clave in (("salon", a.id_salon, a.id_bloque),                       # R3
                      ("profesor", c["profesor"].id, a.id_bloque),              # R4
                      ("grupo", c["grupo"].id, a.id_bloque)):                   # R5
            if clave in vistos:
                return False
            vistos.add(clave)
    return True


if __name__ == "__main__":
    rng = random.Random(5)
    total = iguales = peores = incompletas = invalidas = certificadas = cert_erroneas = 0
    for _ in range(1500):
        d = generar(rng)
        ses = generar_sesiones(d["materias"], d["grupos"])
        if len(ses) > 4:
            continue
        idx = construir_indices(d, ses)
        q_opt, _ = optimo(ses, d, idx)
        if q_opt < 0:
            continue                      # instancia sin solución completa
        r = divide_venceras(ses, d, idx)
        total += 1
        if not es_valida(r["solucion"], d, idx):
            invalidas += 1
        if not r["completa"]:
            incompletas += 1
            continue
        if abs(r["calidad"] - q_opt) < 1e-9:
            iguales += 1
        else:
            peores += 1
        if r["optimo_garantizado"]:
            certificadas += 1
            if abs(r["calidad"] - q_opt) > 1e-9:
                cert_erroneas += 1

    print(f"instancias con óptimo conocido : {total}")
    print(f"iguales al óptimo              : {iguales} ({iguales / total:.1%})")
    print(f"por debajo del óptimo          : {peores}")
    print(f"incompletas (R6)               : {incompletas}")
    print(f"soluciones inválidas           : {invalidas}")
    print(f"óptimo certificado             : {certificadas}")
    print(f"certificados erróneos          : {cert_erroneas}")
