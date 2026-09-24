"""
Formateo de la solución del Planificador de Horarios.

Convierte una lista de Asignacion en un diccionario indexado por salón,
donde cada salón tiene 5 listas (una por día) y cada día tiene 6
posiciones (una por franja horaria). Cada posición es una tupla:

    (materia, profesor, grupo, franja)

o (None, None, None, None) si el bloque está libre.

La franja se representa como string "HH:MM-HH:MM".
"""

from .models.asignacion import Asignacion


DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes"]

FRANJAS = [
    ("06:00", "08:00"),
    ("08:00", "10:00"),
    ("10:00", "12:00"),
    ("12:00", "14:00"),
    ("14:00", "16:00"),
    ("16:00", "18:00"),
]

LIBRE = (None, None, None, None)


def _etiqueta_franja(bloque) -> str:
    """Devuelve 'HH:MM-HH:MM' a partir de un Bloque."""
    return f"{bloque.hora_inicio}-{bloque.hora_fin}"


def formatear_horario(
    asignaciones: list[Asignacion],
    datos: dict,
    indices: dict,
) -> dict:
    """
    Construye el diccionario de salida.

    Parámetros
    ----------
    asignaciones : list[Asignacion]
        La solución devuelta por la fuerza bruta.
    datos : dict
        Salida del cargador. Se usan 'salones' y 'bloques'.
    indices : dict
        Salida de indices.construir_indices. Se usa 'contexto_sesion'.

    """
    contexto_sesion = indices["contexto_sesion"]
    bloques = datos["bloques"]
    salones = datos["salones"]

    bloque_info = {
        b.id: (b.dia, _etiqueta_franja(b))
        for b in bloques
    }

    franja_a_indice = {
        f"{hi}-{hf}": k
        for k, (hi, hf) in enumerate(FRANJAS)
    }

    horario: dict = {}
    for salon in salones:
        horario[salon.id] = [
            [LIBRE for _ in FRANJAS]
            for _ in DIAS
        ]

    for a in asignaciones:
        ctx = contexto_sesion[a.id_sesion]
        materia = ctx["materia"].nombre
        profesor = ctx["profesor"].nombre
        grupo = ctx["grupo"].nombre

        dia, franja_str = bloque_info[a.id_bloque]
        i_dia = DIAS.index(dia)
        i_franja = franja_a_indice[franja_str]

        horario[a.id_salon][i_dia][i_franja] = (
            materia, profesor, grupo, franja_str,
        )

    return horario


def imprimir_horario(horario: dict) -> None:
    """Imprime el horario en consola, salón por salón."""
    for id_salon, dias in horario.items():
        print(f"=== Salón {id_salon} ===")
        for i_dia, dia in enumerate(DIAS):
            print(f"  {dia.capitalize()}:")
            for i_franja, franja in enumerate(FRANJAS):
                hi, hf = franja
                etiqueta = f"{hi}-{hf}"
                contenido = dias[i_dia][i_franja]
                if contenido == LIBRE:
                    print(f"    {etiqueta}  ---")
                else:
                    materia, profesor, grupo, _ = contenido
                    print(f"    {etiqueta}  {materia} | {profesor} | {grupo}")
