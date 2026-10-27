"""
Programación dinámica por bloques para el Planificador de Horarios (Entrega 2).

Idea
----
Las restricciones duras R3, R4 y R5 solo relacionan sesiones que caen en el
MISMO bloque; R1 es individual. Por eso el problema se puede resolver bloque
a bloque, recordando únicamente QUÉ sesiones ya fueron programadas:

    estado : (b, mask)   mask = conjunto de sesiones ya ubicadas (2^S)
    dp[b][mask]          = máxima preferencia acumulada usando los bloques 0..b-1
    transición           = elegir un subconjunto T de sesiones pendientes que
                           quepa en el bloque b (profesores distintos, grupos
                           distintos, salones suficientes) y sumar su valor
    respuesta            = dp[B][todas]   (R6: todas programadas)

Modelo restringido
------------------
La DP optimiza la PREFERENCIA DEL PROFESOR, que es aditiva por (sesión, bloque).
Los términos por pares del mismo grupo (misma franja, mismo salón, días
distintos) y el uso global de salones NO son aditivos: meterlos exigiría
recordar franja/salón/día de cada sesión ya puesta y el estado volvería a
explotar. Por eso el resultado es óptimo para R1–R6 + preferencia, y la
calidad completa (`evaluar_calidad`) se reporta solo como medida.

Asignación de salones dentro de un bloque
-----------------------------------------
Un subconjunto T cabe en un bloque si existe un emparejamiento sesión-salón
con capacidad suficiente. Como R1 es un umbral, basta ordenar las sesiones por
tamaño y los salones por capacidad (ambos de mayor a menor) y comprobar que la
i-ésima sesión cabe en el i-ésimo salón.

Complejidad
-----------
Tiempo  : O(B · 3^S) (cada máscara recorre los subconjuntos de su complemento).
Espacio : O(B · 2^S) por los punteros de reconstrucción.

Uso (desde la raíz del proyecto):
    python -m src.dinamica
"""

from __future__ import annotations

from .calidad import evaluar_calidad
from .models.asignacion import Asignacion

_PREF_VALOR = {0: 0.0, 1: 0.5, 2: 1.0}

# Penalización mínima por cada par de sesiones en el mismo bloque. Es tan
# pequeña (S² · EPS < 0.5 para S <= 20) que nunca cambia la preferencia
# óptima; solo desempata hacia horarios que usan menos salones a la vez.
_EPS_DESEMPATE = 1e-3


def _asignar_salones(sesiones_mask: list[int], tamanos: list[int], salones_ord: list):
    """
    Empareja las sesiones (índices) con salones. Devuelve {indice_sesion: salon}
    o None si no caben. `salones_ord` va de mayor a menor capacidad.
    """
    if len(sesiones_mask) > len(salones_ord):
        return None
    ordenadas = sorted(sesiones_mask, key=lambda i: -tamanos[i])
    resultado = {}
    for i, salon in zip(ordenadas, salones_ord):
        if salon.capacidad < tamanos[i]:
            return None
        resultado[i] = salon
    return resultado


def dinamica(sesiones: list, datos: dict, indices: dict) -> dict:
    """
    Parámetros
    ----------
    sesiones : list[Sesion]
    datos    : dict (salida de cargar_datos)
    indices  : dict (salida de construir_indices)

    Retorna
    -------
    dict con:
        solucion          : list[Asignacion] | None
        calidad           : float   (evaluar_calidad de la solución)
        valor_preferencia : float   (objetivo de la DP: suma de preferencias)
        estados_explorados: int     (pares (bloque, máscara) alcanzados)
        mascaras_factibles: int     (subconjuntos que caben en un bloque)
        completa          : bool
    """
    contexto = indices["contexto_sesion"]
    bloques = datos["bloques"]
    bloques_por_id = {b.id: b for b in bloques}
    salones_ord = sorted(datos["salones"], key=lambda s: -s.capacidad)

    n = len(sesiones)
    if n == 0:
        return {
            "solucion": [], "calidad": 0.0, "valor_preferencia": 0.0,
            "estados_explorados": 0, "mascaras_factibles": 0, "completa": True,
        }

    profs = [contexto[s.id]["profesor"].id for s in sesiones]
    grupos = [contexto[s.id]["grupo"].id for s in sesiones]
    tamanos = [contexto[s.id]["grupo"].cantidad_de_estudiantes for s in sesiones]

    # Subconjuntos que caben en UN bloque (independiente del bloque concreto).
    total = 1 << n
    factible = bytearray(total)
    factible[0] = 1
    for mask in range(1, total):
        bajo = mask & -mask
        resto = mask ^ bajo
        if not factible[resto]:
            continue
        i = bajo.bit_length() - 1
        miembros = [j for j in range(n) if mask >> j & 1]
        if any(j != i and (profs[j] == profs[i] or grupos[j] == grupos[i])
               for j in miembros):
            continue
        if _asignar_salones(miembros, tamanos, salones_ord) is None:
            continue
        factible[mask] = 1
    mascaras_factibles = sum(factible) - 1

    # valor[b][i] = preferencia del profesor de la sesión i en el bloque b.
    valor = [
        [_PREF_VALOR.get(contexto[s.id]["profesor"].preferencias.get(b.id, 1), 0.5)
         for s in sesiones]
        for b in bloques
    ]

    def valor_subconjunto(b: int, mask: int) -> float:
        fila = valor[b]
        miembros = [i for i in range(n) if mask >> i & 1]
        k = len(miembros)
        # Desempate: penaliza sesiones simultáneas (cada una ocupa otro salón).
        return sum(fila[i] for i in miembros) - _EPS_DESEMPATE * k * (k - 1) / 2

    todas = total - 1
    dp: dict[int, float] = {0: 0.0}
    padres: list[dict[int, tuple[int, int]]] = []  # por bloque: mask -> (mask_prev, T)
    estados = 1

    for b in range(len(bloques)):
        nuevo: dict[int, float] = {}
        padre: dict[int, tuple[int, int]] = {}
        for mask, v in dp.items():
            # Opción vacía: no usar este bloque.
            if nuevo.get(mask, -1.0) < v:
                nuevo[mask] = v
                padre[mask] = (mask, 0)
            comp = todas ^ mask
            sub = comp
            while sub:
                if factible[sub]:
                    m2 = mask | sub
                    v2 = v + valor_subconjunto(b, sub)
                    if v2 > nuevo.get(m2, -1.0):
                        nuevo[m2] = v2
                        padre[m2] = (mask, sub)
                sub = (sub - 1) & comp
        dp = nuevo
        padres.append(padre)
        estados += len(dp)

    if todas not in dp:
        return {
            "solucion": None, "calidad": 0.0, "valor_preferencia": 0.0,
            "estados_explorados": estados, "mascaras_factibles": mascaras_factibles,
            "completa": False,
        }

    # Reconstrucción hacia atrás.
    solucion: list[Asignacion] = []
    preferencia = 0.0
    mask = todas
    for b in range(len(bloques) - 1, -1, -1):
        prev, sub = padres[b][mask]
        if sub:
            miembros = [i for i in range(n) if sub >> i & 1]
            preferencia += sum(valor[b][i] for i in miembros)
            salones = _asignar_salones(miembros, tamanos, salones_ord)
            for i in miembros:
                solucion.append(Asignacion(
                    id_sesion=sesiones[i].id,
                    id_salon=salones[i].id,
                    id_bloque=bloques[b].id,
                ))
        mask = prev

    return {
        "solucion": solucion,
        "calidad": evaluar_calidad(solucion, indices, bloques_por_id),
        "valor_preferencia": preferencia,
        "estados_explorados": estados,
        "mascaras_factibles": mascaras_factibles,
        "completa": len(solucion) == n,
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
        r = dinamica(sesiones, d, idx)
        t1 = time.perf_counter()

        print(f"{caso}:")
        print(f"  sesiones              : {len(sesiones)}")
        print(f"  solucion completa     : {r['completa']}")
        print(f"  calidad               : {r['calidad']:.4f}")
        print(f"  valor preferencia     : {r['valor_preferencia']:.2f}")
        print(f"  estados explorados    : {r['estados_explorados']}")
        print(f"  tiempo                : {t1 - t0:.6f} s")
        print()
