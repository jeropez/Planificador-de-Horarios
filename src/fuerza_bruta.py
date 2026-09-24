"""
Fuerza bruta pura con selección por calidad para el Planificador de Horarios.

Estrategia:
    1. Generar TODAS las combinaciones del producto cartesiano
       (bloque, salón) para cada sesión. Sin poda ni backtracking.
    2. Para cada combinación, verificar R1–R5.
    3. De las combinaciones válidas, calcular calidad con evaluar_calidad.
    4. Devolver la de mayor calidad.

Las preferencias blandas no son obligatorias: si no existe ninguna
solución que las satisfaga, se devuelve la mejor posible dentro de las
válidas. La calidad solo ordena soluciones ya válidas.
"""

from itertools import product

from .calidad import evaluar_calidad
from .models.asignacion import Asignacion
from .validaciones import (
    cumple_r1_capacidad,
    hay_conflicto_grupo,
    hay_conflicto_profesor,
    hay_conflicto_salon,
)


def _es_valida(asignaciones: list[Asignacion], indices: dict) -> bool:
    """Verifica R1, R3, R4, R5 sobre una combinación completa."""
    contexto = indices["contexto_sesion"]
    vistas: list[Asignacion] = []

    for a in asignaciones:
        ctx = contexto[a.id_sesion]
        grupo = ctx["grupo"]
        profesor = ctx["profesor"]

        if hay_conflicto_salon(vistas, a.id_salon, a.id_bloque):
            return False
        if hay_conflicto_profesor(vistas, contexto, profesor.id, a.id_bloque):
            return False
        if hay_conflicto_grupo(vistas, contexto, grupo.id, a.id_bloque):
            return False

        vistas.append(a)

    return True


def fuerza_bruta(
    sesiones: list,
    datos: dict,
    indices: dict,
) -> dict:
    """
    Recorre todas las combinaciones y devuelve la mejor solución válida.

    Parámetros
    ----------
    sesiones : list[Sesion]
    datos    : dict con 'bloques' y 'salones'
    indices  : dict de indices.construir_indices

    Retorna
    -------
    dict con:
        solucion              : list[Asignacion] | None
        calidad               : float
        soluciones_encontradas: int
        combinaciones_probadas: int
    """
    contexto = indices["contexto_sesion"]
    bloques = datos["bloques"]
    salones = datos["salones"]
    bloques_por_id = {b.id: b for b in bloques}

    # Todas las opciones por sesión: (bloque, salón)
    opciones_por_sesion = [
        [(bloque, salon) for bloque in bloques for salon in salones]
        for _ in sesiones
    ]

    mejor_solucion: list[Asignacion] | None = None
    mejor_calidad = -1.0
    soluciones_encontradas = 0
    combinaciones_probadas = 0

    for combinacion in product(*opciones_por_sesion):
        combinaciones_probadas += 1

        # Construir asignaciones, validando R1 en el camino
        asignaciones: list[Asignacion] = []
        valida = True
        for sesion, (bloque, salon) in zip(sesiones, combinacion):
            grupo = contexto[sesion.id]["grupo"]
            if not cumple_r1_capacidad(salon, grupo):
                valida = False
                break
            asignaciones.append(
                Asignacion(
                    id_sesion=sesion.id,
                    id_salon=salon.id,
                    id_bloque=bloque.id,
                )
            )

        if not valida:
            continue

        if not _es_valida(asignaciones, indices):
            continue

        soluciones_encontradas += 1

        calidad = evaluar_calidad(asignaciones, indices, bloques_por_id)
        if calidad > mejor_calidad:
            mejor_calidad = calidad
            mejor_solucion = list(asignaciones)

    return {
        "solucion": mejor_solucion,
        "calidad": mejor_calidad if mejor_solucion is not None else 0.0,
        "soluciones_encontradas": soluciones_encontradas,
        "combinaciones_probadas": combinaciones_probadas,
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
        resultado = fuerza_bruta(sesiones, d, idx)
        t1 = time.perf_counter()

        print(f"{caso}:")
        print(f"  sesiones              : {len(sesiones)}")
        print(f"  solucion encontrada   : {resultado['solucion'] is not None}")
        print(f"  calidad               : {resultado['calidad']:.4f}")
        print(f"  soluciones encontradas: {resultado['soluciones_encontradas']}")
        print(f"  combinaciones probadas: {resultado['combinaciones_probadas']}")
        print(f"  tiempo                : {t1 - t0:.6f} s")
        print()