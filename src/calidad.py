"""
Función de calidad del Planificador de Horarios.

Evalúa una solución completa (lista de Asignacion) según preferencias
blandas. Devuelve un valor normalizado en [0, 1].

Componentes:
    1. Preferencia horaria del profesor (0/1/2 -> 0.0/0.5/1.0).
    2. Sesiones del mismo grupo en la misma franja horaria.
    3. Sesiones del mismo grupo en el mismo salón.
    4. Sesiones del mismo grupo en días distintos.
    5. Uso eficiente de salones.

Los criterios 2, 3 y 4 se calculan por pares del mismo grupo. Si un
grupo tiene una sola sesión, no aporta pares y esa componente se omite
del promedio (no penaliza ni beneficia).
"""

from itertools import combinations

from .models.asignacion import Asignacion


PESOS = {
    "preferencia":    0.30,
    "misma_franja":   0.20,
    "mismo_salon":    0.20,
    "dias_distintos": 0.20,
    "uso_salones":    0.10,
}


def _franja(bloque) -> tuple[str, str]:
    """Devuelve (hora_inicio, hora_fin) del bloque."""
    return (bloque.hora_inicio, bloque.hora_fin)


def _preferencia_a_valor(p: int) -> float:
    """Mapea 0/1/2 a 0.0/0.5/1.0."""
    return {0: 0.0, 1: 0.5, 2: 1.0}.get(p, 0.5)


def evaluar_calidad(
    asignaciones: list[Asignacion],
    indices: dict,
    bloques_por_id: dict,
    pesos: dict | None = None,
) -> float:
    """
    Calcula la calidad normalizada de una solución.

    Parámetros
    ----------
    asignaciones : list[Asignacion]
    indices : dict
        Salida de indices.construir_indices. Se usa 'contexto_sesion'.
    bloques_por_id : dict[UUID, Bloque]
        Mapa id_bloque -> Bloque, para consultar la franja y el día.
    pesos : dict | None
        Si None, usa PESOS.

    Retorna
    -------
    float en [0, 1].
    """
    if pesos is None:
        pesos = PESOS

    if not asignaciones:
        return 0.0

    contexto = indices["contexto_sesion"]

    suma_pref = 0.0
    for a in asignaciones:
        profesor = contexto[a.id_sesion]["profesor"]
        valor = profesor.preferencias.get(a.id_bloque, 1)
        suma_pref += _preferencia_a_valor(valor)
    calidad_pref = suma_pref / len(asignaciones)

    grupos: dict[tuple, list[Asignacion]] = {}
    for a in asignaciones:
        ctx = contexto[a.id_sesion]
        clave = (ctx["materia"].id, ctx["grupo"].id)
        grupos.setdefault(clave, []).append(a)

    pares_totales = 0
    pares_misma_franja = 0
    pares_mismo_salon = 0
    pares_dias_distintos = 0

    for asigs in grupos.values():
        for a1, a2 in combinations(asigs, 2):
            pares_totales += 1
            b1 = bloques_por_id[a1.id_bloque]
            b2 = bloques_por_id[a2.id_bloque]

            if _franja(b1) == _franja(b2):
                pares_misma_franja += 1
            if a1.id_salon == a2.id_salon:
                pares_mismo_salon += 1
            if b1.dia != b2.dia:
                pares_dias_distintos += 1

    if pares_totales > 0:
        calidad_franja = pares_misma_franja / pares_totales
        calidad_salon = pares_mismo_salon / pares_totales
        calidad_dias = pares_dias_distintos / pares_totales
    else:
        calidad_franja = None
        calidad_salon = None
        calidad_dias = None

    salones_usados = len({a.id_salon for a in asignaciones})
    calidad_uso = 1.0 / salones_usados if salones_usados > 0 else 0.0

    componentes = [
        (pesos["preferencia"],    calidad_pref),
        (pesos["misma_franja"],   calidad_franja),
        (pesos["mismo_salon"],    calidad_salon),
        (pesos["dias_distintos"], calidad_dias),
        (pesos["uso_salones"],    calidad_uso),
    ]

    peso_total = 0.0
    suma = 0.0
    for peso, valor in componentes:
        if valor is None:
            continue
        peso_total += peso
        suma += peso * valor

    if peso_total == 0.0:
        return 0.0

    return suma / peso_total