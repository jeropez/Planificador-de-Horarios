"""
Solución GREEDY para el Planificador de Horarios (Entrega 2).

Decisión local óptima
---------------------
El algoritmo toma dos decisiones, ambas irrevocables (sin retroceso):

  1. ¿QUÉ sesión asigno ahora?
       La más restringida: la que tiene menos opciones (bloque, salón)
       factibles con el tablero vacío (R1). Desempate: grupo más grande
       primero, porque necesita los salones de mayor capacidad.

  2. ¿DÓNDE la asigno?
       Entre las opciones que cumplen R1, R3, R4 y R5, la que MAXIMIZA la
       calidad parcial, calculada con la misma `evaluar_calidad` que usa
       la fuerza bruta. Así greedy y fuerza bruta optimizan exactamente
       el mismo objetivo y la comparación es justa.
       Desempates: menor capacidad desperdiciada (best-fit) y, por último,
       el orden original de bloques/salones (para ser determinista).

Una sesión ya colocada NO se mueve. Si una sesión no tiene ninguna opción
factible, queda sin asignar (R6 se incumple) y se reporta.

Uso (desde la raíz del proyecto):
    python -m src.greedy
"""

from __future__ import annotations

from uuid import UUID

from .calidad import evaluar_calidad
from .models.asignacion import Asignacion


def greedy(sesiones: list, datos: dict, indices: dict) -> dict:
    """
    Parámetros
    ----------
    sesiones : list[Sesion]          (salida de generar_sesiones)
    datos    : dict                  (salida de cargar_datos)
    indices  : dict                  (salida de construir_indices)

    Retorna
    -------
    dict con:
        solucion              : list[Asignacion]  (solo las que se lograron ubicar)
        calidad               : float
        no_asignadas          : list[Sesion]      (vacía si se cumple R6)
        completa              : bool              (True si todas quedaron asignadas)
        candidatos_evaluados  : int               (equivalente a "combinaciones_probadas")
    """
    contexto = indices["contexto_sesion"]
    bloques = datos["bloques"]
    salones = datos["salones"]
    bloques_por_id = {b.id: b for b in bloques}

    # Tableros de ocupación: comprobar un conflicto cuesta O(1).
    # Los ids de bloque ya incluyen el día (un Bloque = día + franja).
    prof_ocupado: set[tuple[UUID, UUID]] = set()    # (id_profesor, id_bloque)  -> R4
    grupo_ocupado: set[tuple[UUID, UUID]] = set()   # (id_grupo,    id_bloque)  -> R5
    salon_ocupado: set[tuple[str, UUID]] = set()    # (id_salon,    id_bloque)  -> R3

    def opciones_factibles(sesion) -> list[tuple]:
        """Todas las (bloque, salón) donde la sesión cabe sin romper R1, R3, R4, R5."""
        ctx = contexto[sesion.id]
        id_prof = ctx["profesor"].id
        id_grupo = ctx["grupo"].id
        n_estudiantes = ctx["grupo"].cantidad_de_estudiantes

        ops = []
        for bloque in bloques:
            if (id_prof, bloque.id) in prof_ocupado:       # R4
                continue
            if (id_grupo, bloque.id) in grupo_ocupado:     # R5
                continue
            for salon in salones:
                if salon.capacidad < n_estudiantes:        # R1
                    continue
                if (salon.id, bloque.id) in salon_ocupado:  # R3
                    continue
                ops.append((bloque, salon))
        return ops

    # ---- Decisión local 1: ORDEN de las sesiones (más restringida primero).
    # Se calcula una sola vez con el tablero vacío.
    orden = sorted(
        sesiones,
        key=lambda s: (
            len(opciones_factibles(s)),
            -contexto[s.id]["grupo"].cantidad_de_estudiantes,
        ),
    )

    solucion: list[Asignacion] = []
    no_asignadas: list = []
    candidatos_evaluados = 0

    for sesion in orden:
        ctx = contexto[sesion.id]
        n_estudiantes = ctx["grupo"].cantidad_de_estudiantes
        ops = opciones_factibles(sesion)   # se recalcula: el tablero ya cambió

        if not ops:
            no_asignadas.append(sesion)    # sin retroceso: se queda sin lugar
            continue

        # ---- Decisión local 2: DÓNDE colocarla (maximizar calidad parcial).
        mejor_clave = None
        mejor_op = None
        for pos, (bloque, salon) in enumerate(ops):
            candidata = Asignacion(
                id_sesion=sesion.id, id_salon=salon.id, id_bloque=bloque.id
            )
            calidad_parcial = evaluar_calidad(
                solucion + [candidata], indices, bloques_por_id
            )
            candidatos_evaluados += 1

            desperdicio = salon.capacidad - n_estudiantes
            # clave: mayor calidad, luego menor desperdicio, luego orden original
            clave = (-calidad_parcial, desperdicio, pos)
            if mejor_clave is None or clave < mejor_clave:
                mejor_clave = clave
                mejor_op = (bloque, salon)

        bloque, salon = mejor_op
        solucion.append(
            Asignacion(id_sesion=sesion.id, id_salon=salon.id, id_bloque=bloque.id)
        )
        prof_ocupado.add((ctx["profesor"].id, bloque.id))
        grupo_ocupado.add((ctx["grupo"].id, bloque.id))
        salon_ocupado.add((salon.id, bloque.id))

    return {
        "solucion": solucion,
        "calidad": evaluar_calidad(solucion, indices, bloques_por_id) if solucion else 0.0,
        "no_asignadas": no_asignadas,
        "completa": not no_asignadas,
        "candidatos_evaluados": candidatos_evaluados,
    }


if __name__ == "__main__":
    import time

    from .cargador import cargar_datos
    from .generar_sesiones import generar_sesiones
    from .indices import construir_indices

    for caso in ["caso_pequeno", "caso_mediano", "caso_grande"]:
        d = cargar_datos(f"datos/{caso}.json")
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)

        t0 = time.perf_counter()
        r = greedy(sesiones, d, idx)
        t1 = time.perf_counter()

        print(f"{caso}:")
        print(f"  sesiones              : {len(sesiones)}")
        print(f"  solucion completa     : {r['completa']}")
        print(f"  calidad               : {r['calidad']:.4f}")
        print(f"  candidatos evaluados  : {r['candidatos_evaluados']}")
        print(f"  tiempo                : {t1 - t0:.6f} s")
        print()
