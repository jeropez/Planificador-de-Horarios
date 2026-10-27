"""
Divide y vencerás por materia para el Planificador de Horarios.

Idea
----
Cada profesor enseña una sola materia (R7) y cada grupo ve una sola materia.
Por eso dos sesiones de materias DISTINTAS nunca comparten profesor (R4) ni
grupo (R5), y nunca forman un par en la función de calidad (los pares son
siempre del mismo grupo). Lo único que las relaciona es R3 (salón ocupado)
y el término global de uso de salones.

    DIVIDIR   : separar las sesiones por materia.
    VENCER    : resolver cada materia de forma exacta (subproblema pequeño).
    COMBINAR  : unir recursivamente mitades del conjunto de materias. Si en
                algún bloque hay más clases de las que caben en los salones,
                se REPARA cambiando una materia a su siguiente mejor
                alternativa (la que menos calidad pierde).

Subproblema de una materia
--------------------------
Todas sus sesiones comparten profesor, así que van en bloques distintos y
entre ellas nunca chocan por salón. Entonces:
  - lo mejor para "mismo salón" es dejar cada grupo en un único salón, y
  - solo hay que escoger QUÉ bloques usa cada grupo (las sesiones de un mismo
    grupo son intercambiables): combinaciones de bloques, no permutaciones.

El puntaje de una elección es exactamente la parte de `evaluar_calidad` que
depende de esa materia (preferencia + pares de misma franja, mismo salón y
días distintos), con los mismos pesos y denominadores globales. Por eso, si
al combinar no hay reparaciones y cada grupo conserva un solo salón, el
horario es ÓPTIMO en el 90 % del peso de la calidad; solo el uso global de
salones (10 %) queda fuera del óptimo garantizado.

Se buscan las K mejores alternativas por materia con ramificación y poda
(top-K); la mejor es la solución del subproblema y el resto sirve para
reparar choques al combinar.

Complejidad
-----------
Con M materias de s sesiones cada una (un grupo por materia):
  Vencer   : O(M · C(B, s) · s²)   (combinaciones de bloques por materia)
  Combinar : O(S · log M) por nivel de la recursión, más las reparaciones.
Frente a O((B·A)^S · S²) de la fuerza bruta: el exponente pasa de S (todas
las sesiones) a s (las de una materia).

Uso (desde la raíz del proyecto):
    python -m src.divide_venceras
"""

from __future__ import annotations

import heapq
from itertools import combinations

from .calidad import PESOS, evaluar_calidad
from .models.asignacion import Asignacion

_PREF_VALOR = {0: 0.0, 1: 0.5, 2: 1.0}

# Alternativas que se guardan por materia para reparar choques al combinar.
K_ALTERNATIVAS = 50


def _cabe(tamanos: list[int], capacidades_desc: list[int]) -> bool:
    """¿Se pueden ubicar estos grupos en salones distintos de un bloque? (R1, R3)"""
    if len(tamanos) > len(capacidades_desc):
        return False
    return all(t <= c for t, c in zip(sorted(tamanos, reverse=True), capacidades_desc))


def divide_venceras(sesiones: list, datos: dict, indices: dict) -> dict:
    """
    Parámetros
    ----------
    sesiones : list[Sesion]
    datos    : dict (salida de cargar_datos)
    indices  : dict (salida de construir_indices)

    Retorna
    -------
    dict con:
        solucion                : list[Asignacion]
        calidad                 : float
        completa                : bool
        subproblemas            : int   (materias resueltas por separado)
        combinaciones_evaluadas : int   (trabajo: elecciones de bloques puntuadas)
        reparaciones            : int   (cambios de alternativa al combinar)
        optimo_garantizado      : bool  (sin reparaciones y cada grupo en un salón)
    """
    contexto = indices["contexto_sesion"]
    bloques = datos["bloques"]
    salones = datos["salones"]
    bloques_por_id = {b.id: b for b in bloques}
    capacidades_desc = sorted((s.capacidad for s in salones), reverse=True)
    nb = len(bloques)

    vacio = {
        "solucion": [], "calidad": 0.0, "completa": True, "subproblemas": 0,
        "combinaciones_evaluadas": 0, "reparaciones": 0, "optimo_garantizado": True,
    }
    if not sesiones:
        return vacio

    # ------------------------------------------------------------- DIVIDIR
    # materia -> grupo -> sesiones del grupo
    por_materia: dict = {}
    for s in sesiones:
        ctx = contexto[s.id]
        por_materia.setdefault(ctx["materia"].id, {}).setdefault(ctx["grupo"].id, []).append(s)
    materias = list(por_materia)

    # Pesos globales: los mismos que usa evaluar_calidad, con sus denominadores.
    total_pares = sum(
        len(ss) * (len(ss) - 1) // 2 for grupos in por_materia.values() for ss in grupos.values()
    )
    w_pref = PESOS["preferencia"] / len(sesiones)
    w_franja = PESOS["misma_franja"] / total_pares if total_pares else 0.0
    w_salon = PESOS["mismo_salon"] / total_pares if total_pares else 0.0
    w_dias = PESOS["dias_distintos"] / total_pares if total_pares else 0.0

    franja = [(b.hora_inicio, b.hora_fin) for b in bloques]
    dia = [b.dia for b in bloques]
    trabajo = 0

    # ------------------------------------------------------------- VENCER
    def opciones_grupo(id_grupo, n_ses):
        """Todas las combinaciones de n_ses bloques para un grupo, con su puntaje."""
        nonlocal trabajo
        grupo = contexto[contexto_por_grupo[id_grupo]]["grupo"]
        prof = contexto[contexto_por_grupo[id_grupo]]["profesor"]
        if grupo.cantidad_de_estudiantes > capacidades_desc[0]:
            return []  # ningún salón le sirve (R1)
        pref = [_PREF_VALOR.get(prof.preferencias.get(b.id, 1), 0.5) for b in bloques]
        ops = []
        for combo in combinations(range(nb), n_ses):
            trabajo += 1
            p = w_pref * sum(pref[i] for i in combo)
            for i, j in combinations(combo, 2):
                p += w_salon  # el grupo queda en un único salón
                if franja[i] == franja[j]:
                    p += w_franja
                if dia[i] != dia[j]:
                    p += w_dias
            ops.append((p, combo))
        ops.sort(key=lambda x: -x[0])
        return ops

    contexto_por_grupo = {}
    for s in sesiones:
        contexto_por_grupo.setdefault(contexto[s.id]["grupo"].id, s.id)

    def mejores_alternativas(id_materia):
        """
        Top-K elecciones de bloques para la materia (grupos en bloques
        disjuntos, porque comparten profesor). Ramificación y poda.
        """
        grupos = list(por_materia[id_materia].items())
        listas = [opciones_grupo(g, len(ss)) for g, ss in grupos]
        if any(not l for l in listas):
            return [], [g for g, _ in grupos]
        mejor_resto = [0.0] * (len(listas) + 1)
        for i in range(len(listas) - 1, -1, -1):
            mejor_resto[i] = mejor_resto[i + 1] + listas[i][0][0]

        heap: list = []  # min-heap de (puntaje, contador, elección)
        contador = [0]

        def dfs(i, usados, puntaje, eleccion):
            if i == len(listas):
                contador[0] += 1
                item = (puntaje, contador[0], tuple(eleccion))
                if len(heap) < K_ALTERNATIVAS:
                    heapq.heappush(heap, item)
                elif puntaje > heap[0][0]:
                    heapq.heapreplace(heap, item)
                return
            for p, combo in listas[i]:
                if len(heap) == K_ALTERNATIVAS and puntaje + p + mejor_resto[i + 1] <= heap[0][0]:
                    break  # las siguientes son peores: poda
                if usados.isdisjoint(combo):
                    eleccion.append(combo)
                    dfs(i + 1, usados | set(combo), puntaje + p, eleccion)
                    eleccion.pop()

        dfs(0, frozenset(), 0.0, [])
        alternativas = sorted(heap, key=lambda x: -x[0])
        return [(p, {g: el[k] for k, (g, _) in enumerate(grupos)}) for p, _, el in alternativas], []

    alternativas = {}
    sin_lugar = []
    for m in materias:
        alts, fallidos = mejores_alternativas(m)
        if alts:
            alternativas[m] = alts
        sin_lugar.extend(fallidos)
    eleccion = {m: 0 for m in alternativas}  # índice de la alternativa usada

    # ------------------------------------------------------------- COMBINAR
    tamano = {g: contexto[sid]["grupo"].cantidad_de_estudiantes for g, sid in contexto_por_grupo.items()}
    w_uso = PESOS["uso_salones"]
    reparaciones = 0
    ajustes = 0

    def ocupacion(ms, cambio=None):
        """bloque -> tamaños de los grupos que lo usan, para las materias ms."""
        occ: dict[int, list[int]] = {}
        for m in ms:
            idx = cambio[1] if cambio and cambio[0] == m else eleccion[m]
            for g, combo in alternativas[m][idx][1].items():
                for b in combo:
                    occ.setdefault(b, []).append(tamano[g])
        return occ

    def choques(ms, cambio=None):
        return [b for b, ts in ocupacion(ms, cambio).items() if not _cabe(ts, capacidades_desc)]

    def salones_necesarios(ms, cambio=None):
        """Máximo de clases simultáneas: cota inferior de los salones usados."""
        return max((len(ts) for ts in ocupacion(ms, cambio).values()), default=1)

    def ajustar_salones(union: list) -> None:
        """
        El uso de salones es global: ninguna materia lo ve por separado. Se
        cambia una materia a otra alternativa si la ganancia en uso de salones
        supera lo que pierde en su propio puntaje (búsqueda local).
        """
        nonlocal ajustes
        while True:
            r_actual = salones_necesarios(union)
            if r_actual <= 1:
                return
            mejor = None  # (ganancia, materia, índice)
            for m in union:
                actual = alternativas[m][eleccion[m]][0]
                for k in range(len(alternativas[m])):
                    if k == eleccion[m] or choques(union, (m, k)):
                        continue
                    r_nuevo = salones_necesarios(union, (m, k))
                    ganancia = (alternativas[m][k][0] - actual) + w_uso * (1 / r_nuevo - 1 / r_actual)
                    if ganancia > 1e-12 and (mejor is None or ganancia > mejor[0]):
                        mejor = (ganancia, m, k)
            if mejor is None:
                return
            _, m, k = mejor
            eleccion[m] = k
            ajustes += 1

    def combinar(izq: list, der: list) -> list:
        nonlocal reparaciones
        union = izq + der
        while True:
            malos = set(choques(union))
            if not malos:
                ajustar_salones(union)
                return union
            # Materias involucradas en los bloques con choque (primero la mitad derecha).
            implicadas = [
                m for m in der + izq
                if any(b in malos for combo in alternativas[m][eleccion[m]][1].values() for b in combo)
            ]
            mejor = None  # (pérdida, materia, índice)
            for m in implicadas:
                base = alternativas[m][eleccion[m]][0]
                for k in range(eleccion[m] + 1, len(alternativas[m])):
                    perdida = base - alternativas[m][k][0]
                    if mejor and perdida >= mejor[0]:
                        break
                    if len(choques(union, (m, k))) < len(malos):
                        mejor = (perdida, m, k)
                        break
            if mejor is None:
                # Sin alternativa que reduzca los choques: se descarta la materia
                # implicada de la derecha (sus sesiones quedan sin asignar, R6).
                m = implicadas[0]
                sin_lugar.extend(por_materia[m])
                union.remove(m)
                der = [x for x in der if x != m]
                izq = [x for x in izq if x != m]
                continue
            _, m, k = mejor
            eleccion[m] = k
            reparaciones += 1

    def resolver(ms: list) -> list:
        """Divide el conjunto de materias en mitades y las combina."""
        if len(ms) <= 1:
            return ms
        mitad = len(ms) // 2
        return combinar(resolver(ms[:mitad]), resolver(ms[mitad:]))

    finales = resolver(list(alternativas))

    # --------------------------------------------- salones (después de combinar)
    # Cada grupo intenta quedarse en UN salón (mismo salón) y se prefieren los
    # salones ya usados (uso de salones). Grupos grandes primero.
    bloques_grupo = {}
    for m in finales:
        for g, combo in alternativas[m][eleccion[m]][1].items():
            bloques_grupo[g] = combo
    ocupado: dict[tuple[str, int], object] = {}
    salon_de: dict[tuple, str] = {}  # (grupo, bloque) -> salón
    usados: list[str] = []
    grupos_un_salon = 0
    for g in sorted(bloques_grupo, key=lambda x: -tamano[x]):
        combo = bloques_grupo[g]
        candidatos = [s for s in salones if s.capacidad >= tamano[g]
                      and all((s.id, b) not in ocupado for b in combo)]
        candidatos.sort(key=lambda s: (s.id not in usados, s.capacidad))
        if candidatos:
            s = candidatos[0]
            grupos_un_salon += 1
            for b in combo:
                ocupado[(s.id, b)] = g
                salon_de[(g, b)] = s.id
            if s.id not in usados:
                usados.append(s.id)
        else:
            for b in combo:
                libres = sorted((s for s in salones if s.capacidad >= tamano[g] and (s.id, b) not in ocupado),
                                key=lambda s: (s.id not in usados, s.capacidad))
                if libres:
                    ocupado[(libres[0].id, b)] = g
                    salon_de[(g, b)] = libres[0].id
                    if libres[0].id not in usados:
                        usados.append(libres[0].id)

    # Si el reparto voraz dejó a alguien sin salón en un bloque, se reasigna
    # ese bloque completo emparejando por tamaño (siempre cabe: lo verificó combinar).
    por_bloque: dict[int, list] = {}
    for g, combo in bloques_grupo.items():
        for b in combo:
            por_bloque.setdefault(b, []).append(g)
    salones_desc = sorted(salones, key=lambda s: -s.capacidad)
    for b, gs in por_bloque.items():
        if all((g, b) in salon_de for g in gs):
            continue
        for g, s in zip(sorted(gs, key=lambda x: -tamano[x]), salones_desc):
            salon_de[(g, b)] = s.id
        grupos_un_salon -= sum(1 for g in gs if len({salon_de[(g, x)] for x in bloques_grupo[g]}) > 1)

    solucion: list[Asignacion] = []
    for m in finales:
        for g, ss in por_materia[m].items():
            for sesion, b in zip(ss, bloques_grupo[g]):
                solucion.append(Asignacion(
                    id_sesion=sesion.id, id_salon=salon_de[(g, b)], id_bloque=bloques[b].id,
                ))

    completa = len(solucion) == len(sesiones)
    calidad = evaluar_calidad(solucion, indices, bloques_por_id) if solucion else 0.0

    # Cota superior de la calidad: cada materia en su mejor alternativa (no
    # dependen entre sí) más el máximo posible del uso de salones (1 salón).
    # Si la solución la alcanza, es óptima aunque haya habido ajustes.
    peso_total = PESOS["preferencia"] + PESOS["uso_salones"] + (
        PESOS["misma_franja"] + PESOS["mismo_salon"] + PESOS["dias_distintos"] if total_pares else 0.0)
    cota = (sum(alts[0][0] for alts in alternativas.values()) + w_uso) / peso_total
    return {
        "solucion": solucion,
        "calidad": calidad,
        "completa": completa,
        "subproblemas": len(materias),
        "combinaciones_evaluadas": trabajo,
        "reparaciones": reparaciones,
        "ajustes_salones": ajustes,
        "cota_superior": min(cota, 1.0),
        "optimo_garantizado": completa and not sin_lugar and calidad >= cota - 1e-9,
    }


if __name__ == "__main__":
    import time

    from .cargador import cargar_datos
    from .generar_sesiones import generar_sesiones
    from .indices import construir_indices

    for caso in ["caso_pequeno", "caso_mediano", "caso_grande",
                 "caso_multi_pequeno", "caso_multi_mediano", "caso_multi_grande"]:
        d = cargar_datos(f"datos/{caso}.json")
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)

        t0 = time.perf_counter()
        r = divide_venceras(sesiones, d, idx)
        t1 = time.perf_counter()

        print(f"{caso}:")
        print(f"  sesiones                : {len(sesiones)}")
        print(f"  subproblemas (materias) : {r['subproblemas']}")
        print(f"  solucion completa       : {r['completa']}")
        print(f"  calidad                 : {r['calidad']:.4f}")
        print(f"  combinaciones evaluadas : {r['combinaciones_evaluadas']}")
        print(f"  reparaciones            : {r['reparaciones']}")
        print(f"  ajustes de salones      : {r['ajustes_salones']}")
        print(f"  cota superior           : {r['cota_superior']:.4f}")
        print(f"  optimo garantizado      : {r['optimo_garantizado']}")
        print(f"  tiempo                  : {t1 - t0:.6f} s")
        print()
