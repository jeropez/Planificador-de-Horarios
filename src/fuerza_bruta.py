from itertools import product

from .models.asignacion import Asignacion
from .validaciones import (
    cumple_r1_capacidad,
    hay_conflicto_grupo,
    hay_conflicto_profesor,
    hay_conflicto_salon,
)


def _es_valida(asignaciones: list[Asignacion], indices: dict) -> bool:
    """
    Verifica si una combinación completa satisface todas las restricciones.
    Se aplica al final, no durante la generación.
    """
    contexto_sesion = indices["contexto_sesion"]
    vistas: list[Asignacion] = []

    for a in asignaciones:
        ctx = contexto_sesion[a.id_sesion]
        grupo = ctx["grupo"]
        profesor = ctx["profesor"]

        # R1: capacidad del salón
        # (ya se validó antes de generar, pero se puede revalidar aquí)
        # R3: salón libre en ese bloque
        if hay_conflicto_salon(vistas, a.id_salon, a.id_bloque):
            return False
        # R4: profesor libre en ese bloque
        if hay_conflicto_profesor(vistas, contexto_sesion, profesor.id, a.id_bloque):
            return False
        # R5: grupo libre en ese bloque
        if hay_conflicto_grupo(vistas, contexto_sesion, grupo.id, a.id_bloque):
            return False

        vistas.append(a)

    return True


def fuerza_bruta(
    sesiones: list,
    datos: dict,
    indices: dict,
    buscar_optimo: bool = False,
    max_soluciones: int | None = None,
) -> dict:
    """
    Fuerza bruta pura: itera el producto cartesiano completo.

    Parámetros
    ----------
    sesiones : list[Sesion]
    datos    : dict con 'bloques' y 'salones'
    indices  : dict de indices.construir_indices
    buscar_optimo : bool
        Si False, se detiene en la primera solución válida.
        Si True, cuenta todas (o hasta max_soluciones).
    max_soluciones : int | None
        Tope cuando buscar_optimo=True.

    Retorna
    -------
    dict con:
        solucion              : list[Asignacion] | None
        soluciones_encontradas: int
        combinaciones_probadas: int
    """
    contexto_sesion = indices["contexto_sesion"]
    bloques = datos["bloques"]
    salones = datos["salones"]

    # Opciones por sesión: todas las parejas (bloque, salón) sin filtrar nada.
    opciones_por_sesion = [
        [(bloque, salon) for bloque in bloques for salon in salones]
        for _ in sesiones
    ]

    estado = {
        "solucion": None,
        "soluciones_encontradas": 0,
        "combinaciones_probadas": 0,
    }

    for combinacion in product(*opciones_por_sesion):
        estado["combinaciones_probadas"] += 1

        # Construir asignaciones (R1 se verifica aquí, es parte de la validez)
        asignaciones: list[Asignacion] = []
        valida = True
        for sesion, (bloque, salon) in zip(sesiones, combinacion):
            ctx = contexto_sesion[sesion.id]
            grupo = ctx["grupo"]

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

        estado["soluciones_encontradas"] += 1
        if estado["solucion"] is None:
            estado["solucion"] = asignaciones

        if not buscar_optimo:
            break
        if max_soluciones and estado["soluciones_encontradas"] >= max_soluciones:
            break

    return {
        "solucion": estado["solucion"],
        "soluciones_encontradas": estado["soluciones_encontradas"],
        "combinaciones_probadas": estado["combinaciones_probadas"],
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
        resultado = fuerza_bruta(sesiones, d, idx, buscar_optimo=False)
        t1 = time.perf_counter()

        print(f"{caso}:")
        print(f"  sesiones              : {len(sesiones)}")
        print(f"  solucion encontrada   : {resultado['solucion'] is not None}")
        print(f"  soluciones encontradas: {resultado['soluciones_encontradas']}")
        print(f"  combinaciones probadas: {resultado['combinaciones_probadas']}")
        print(f"  tiempo                : {t1 - t0:.6f} s")
        print()