"""
Backtracking con poda para el Planificador de Horarios (Entrega 2).

Estrategia
----------
Exploración en profundidad del árbol de asignaciones, sesión por sesión,
con PODA de ramas inviables. No hay poda por calidad: la calidad se
evalúa solo en las soluciones completas, igual que en fuerza bruta.

Podas implementadas
-------------------
P1. Restricciones duras (R1, R3, R4, R5) al intentar asignar.
    Se validan en el momento, con tableros de ocupación O(1).

P3. Forward checking.
    Antes de entrar a una rama, se verifica que cada sesión restante
    todavía tenga al menos una opción (bloque, salón) libre que cumpla
    R1, R3, R4 y R5. Si alguna no la tiene, la rama es inviable.

P4. Ordenamiento dinámico (MRV: Minimum Remaining Values).
    En cada nivel se elige primero la sesión con menos opciones factibles
    en el estado actual. Reduce el tamaño del árbol sin perder optimalidad.

Modo
----
- `buscar_optimo=True`  : recorre todo el árbol (con podas) y devuelve
                          la mejor solución encontrada.
- `buscar_optimo=False` : devuelve la PRIMERA solución válida encontrada.

Uso (desde la raíz del proyecto):
    python -m src.backtracking
"""

from __future__ import annotations

from uuid import UUID

from .calidad import evaluar_calidad
from .models.asignacion import Asignacion


def backtracking(
    sesiones: list,
    datos: dict,
    indices: dict,
    buscar_optimo: bool = True,
) -> dict:
    """
    Parámetros
    ----------
    sesiones      : list[Sesion]
    datos         : dict  (salida de cargar_datos)
    indices       : dict  (salida de construir_indices)
    buscar_optimo : bool  (True = mejor solución; False = primera válida)

    Retorna
    -------
    dict con:
        solucion              : list[Asignacion] | None
        calidad               : float
        soluciones_encontradas: int
        nodos_explorados      : int
        podas_aplicadas       : int
        completa              : bool
    """
    contexto = indices["contexto_sesion"]
    bloques = datos["bloques"]
    salones = datos["salones"]
    bloques_por_id = {b.id: b for b in bloques}

    n = len(sesiones)
    if n == 0:
        return {
            "solucion": [],
            "calidad": 0.0,
            "soluciones_encontradas": 1,
            "nodos_explorados": 0,
            "podas_aplicadas": 0,
            "completa": True,
        }

    # Tableros de ocupación: chequeo de conflictos en O(1).
    prof_ocupado: set[tuple[UUID, UUID]] = set()
    grupo_ocupado: set[tuple[UUID, UUID]] = set()
    salon_ocupado: set[tuple[str, UUID]] = set()

    estado = {
        "mejor_solucion": None,
        "mejor_calidad": -1.0,
        "soluciones_encontradas": 0,
        "nodos_explorados": 0,
        "podas_aplicadas": 0,
    }

    def opciones_factibles(sesion) -> list[tuple]:
        """(bloque, salón) que cumplen R1, R3, R4 y R5 en el estado actual."""
        ctx = contexto[sesion.id]
        id_prof = ctx["profesor"].id
        id_grupo = ctx["grupo"].id
        n_est = ctx["grupo"].cantidad_de_estudiantes

        ops = []
        for bloque in bloques:
            if (id_prof, bloque.id) in prof_ocupado:
                continue
            if (id_grupo, bloque.id) in grupo_ocupado:
                continue
            for salon in salones:
                if salon.capacidad < n_est:
                    continue
                if (salon.id, bloque.id) in salon_ocupado:
                    continue
                ops.append((bloque, salon))
        return ops

    def forward_checking(pendientes_restantes) -> bool:
        """
        P3: verifica que cada sesión restante tenga al menos una opción.
        Devuelve False si alguna ya no tiene ninguna (rama inviable).
        """
        for s in pendientes_restantes:
            if not opciones_factibles(s):
                return False
        return True

    def backtrack(asignaciones: list[Asignacion], pendientes: list) -> bool:
        """
        Retorna True si debe detenerse toda la búsqueda
        (primera solución encontrada y no se busca el óptimo).
        """
        estado["nodos_explorados"] += 1

        # Caso base: todas las sesiones asignadas
        if not pendientes:
            estado["soluciones_encontradas"] += 1
            calidad = evaluar_calidad(asignaciones, indices, bloques_por_id)

            if calidad > estado["mejor_calidad"]:
                estado["mejor_calidad"] = calidad
                estado["mejor_solucion"] = list(asignaciones)

            if not buscar_optimo:
                return True
            return False

        # P4: elegir la sesión con menos opciones factibles (MRV)
        mejor_idx = -1
        mejor_ops = None
        for i, s in enumerate(pendientes):
            ops = opciones_factibles(s)
            if not ops:
                estado["podas_aplicadas"] += 1
                return False
            if mejor_ops is None or len(ops) < len(mejor_ops):
                mejor_idx = i
                mejor_ops = ops
                if len(ops) == 1:
                    break

        sesion = pendientes[mejor_idx]
        ctx = contexto[sesion.id]
        id_prof = ctx["profesor"].id
        id_grupo = ctx["grupo"].id

        pendientes_restantes = pendientes[:mejor_idx] + pendientes[mejor_idx + 1:]

        for bloque, salon in mejor_ops:
            # P1: aplicar
            asignaciones.append(
                Asignacion(
                    id_sesion=sesion.id,
                    id_salon=salon.id,
                    id_bloque=bloque.id,
                )
            )
            prof_ocupado.add((id_prof, bloque.id))
            grupo_ocupado.add((id_grupo, bloque.id))
            salon_ocupado.add((salon.id, bloque.id))

            # P3: forward checking
            if forward_checking(pendientes_restantes):
                detener = backtrack(asignaciones, pendientes_restantes)
                if detener:
                    asignaciones.pop()
                    prof_ocupado.discard((id_prof, bloque.id))
                    grupo_ocupado.discard((id_grupo, bloque.id))
                    salon_ocupado.discard((salon.id, bloque.id))
                    return True
            else:
                estado["podas_aplicadas"] += 1

            # Deshacer
            asignaciones.pop()
            prof_ocupado.discard((id_prof, bloque.id))
            grupo_ocupado.discard((id_grupo, bloque.id))
            salon_ocupado.discard((salon.id, bloque.id))

        return False

    backtrack([], list(sesiones))

    return {
        "solucion": estado["mejor_solucion"],
        "calidad": estado["mejor_calidad"] if estado["mejor_solucion"] is not None else 0.0,
        "soluciones_encontradas": estado["soluciones_encontradas"],
        "nodos_explorados": estado["nodos_explorados"],
        "podas_aplicadas": estado["podas_aplicadas"],
        "completa": estado["mejor_solucion"] is not None
                    and len(estado["mejor_solucion"]) == n,
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
        r = backtracking(sesiones, d, idx, buscar_optimo=True)
        t1 = time.perf_counter()

        print(f"{caso}:")
        print(f"  sesiones              : {len(sesiones)}")
        print(f"  solucion completa     : {r['completa']}")
        print(f"  calidad               : {r['calidad']:.4f}")
        print(f"  soluciones encontradas: {r['soluciones_encontradas']}")
        print(f"  nodos explorados      : {r['nodos_explorados']}")
        print(f"  podas aplicadas       : {r['podas_aplicadas']}")
        print(f"  tiempo                : {t1 - t0:.6f} s")
        print()
        