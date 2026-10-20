"""
Busca instancias pequeñas donde greedy NO es óptimo, comparándolo contra un
óptimo exhaustivo (misma función de calidad y mismas restricciones R1, R3-R5).

Uso (desde la raíz del proyecto):
    python -m analisis.contraejemplo_greedy
"""
import random
import sys
from itertools import product
from uuid import UUID

sys.path.insert(0, ".")

from src.calidad import evaluar_calidad
from src.generar_sesiones import generar_sesiones
from src.greedy import greedy
from src.indices import construir_indices
from src.models.asignacion import Asignacion
from src.models.bloque import Bloque
from src.models.grupo import Grupo
from src.models.materia import Materia
from src.models.profesor import Profesor
from src.models.salon import Salon

_n = [0]
def uid():
    _n[0] += 1
    return UUID(int=_n[0])


def optimo(sesiones, datos, indices):
    """Exhaustivo: mejor calidad entre soluciones COMPLETAS válidas (R6)."""
    ctx = indices["contexto_sesion"]
    bpid = {b.id: b for b in datos["bloques"]}
    ops = [(b, s) for b in datos["bloques"] for s in datos["salones"]]
    mejor, mejor_sol = -1.0, None
    for comb in product(ops, repeat=len(sesiones)):
        ok, sal, pro, gru, asig = True, set(), set(), set(), []
        for ses, (b, s) in zip(sesiones, comb):
            c = ctx[ses.id]
            if s.capacidad < c["grupo"].cantidad_de_estudiantes: ok = False; break
            k1, k2, k3 = (s.id, b.id), (c["profesor"].id, b.id), (c["grupo"].id, b.id)
            if k1 in sal or k2 in pro or k3 in gru: ok = False; break
            sal.add(k1); pro.add(k2); gru.add(k3)
            asig.append(Asignacion(ses.id, s.id, b.id))
        if ok:
            q = evaluar_calidad(asig, indices, bpid)
            if q > mejor: mejor, mejor_sol = q, asig
    return mejor, mejor_sol


def generar(rng):
    bloques = [Bloque(uid(), d, h, h) for d in ("lunes", "martes") for h in ("06:00", "08:00")]
    salones = [Salon(f"S{i}", rng.choice([20, 30, 40])) for i in range(rng.choice([1, 2]))]
    grupos, materias, profes = {}, [], []
    for i in range(rng.choice([2, 3])):
        gid, mid, pid = uid(), uid(), uid()
        grupos[gid] = Grupo(gid, f"G{i}", rng.choice([15, 25, 35]), mid)
        materias.append(Materia(mid, f"M{i}", pid, [gid], rng.choice([1, 2])))
        profes.append(Profesor(pid, f"P{i}", mid, {b.id: rng.choice([0, 1, 2]) for b in bloques}))
    return {"bloques": bloques, "salones": salones, "profesores": profes,
            "materias": materias, "grupos": grupos}


if __name__ == "__main__":
    rng = random.Random(11)
    peor = None
    for _ in range(3000):
        d = generar(rng)
        ses = generar_sesiones(d["materias"], d["grupos"])
        if len(ses) > 4:
            continue
        idx = construir_indices(d, ses)
        q_opt, _ = optimo(ses, d, idx)
        if q_opt < 0:
            continue                      # instancia sin solución completa
        r = greedy(ses, d, idx)
        q_gr = r["calidad"] if r["completa"] else -1.0
        if q_gr < q_opt - 1e-9:
            brecha = q_opt - max(q_gr, 0)
            if peor is None or (not r["completa"], brecha) > (not peor[2]["completa"], peor[0]):
                peor = (brecha, d, r, q_opt)
    if peor is None:
        print("No se encontró contraejemplo.")
    else:
        brecha, d, r, q_opt = peor
        print(f"greedy completa={r['completa']}  calidad greedy={r['calidad']:.4f}  óptimo={q_opt:.4f}")
        print("salones   :", [(s.id, s.capacidad) for s in d["salones"]])
        print("grupos    :", [(g.nombre, g.cantidad_de_estudiantes) for g in d["grupos"].values()])
        print("materias  :", [(m.nombre, m.sesiones_semanales) for m in d["materias"]])
        bl = [(b.dia, b.hora_inicio) for b in d["bloques"]]
        print("bloques   :", bl)
        for p in d["profesores"]:
            print(" ", p.nombre, [p.preferencias[b.id] for b in d["bloques"]])
