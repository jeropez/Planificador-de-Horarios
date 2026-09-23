"""
Generador de datos de prueba para el Planificador de Horarios.

Genera tres archivos JSON en la carpeta `datos/`:
    - caso_pequeno.json
    - caso_mediano.json
    - caso_grande.json
"""

import json
import random
from pathlib import Path
from uuid import uuid4

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes"]

NOMBRES_MATERIAS = [
    "Cálculo en Varias Variables",
    "Análisis y Diseño de Algoritmos",
    "Modelos de Datos",
    "Ecuaciones Diferenciales",
    "Estadística",
    "Fundamentos de Diseño de Software",
    "Estructuras de Datos",
    "Cálculo Integral",
    "Álgebra Lineal",
    "Física Mecánica",
    "Programación Orientada a Objetos",
    "Bases de Datos",
    "Redes de Computadores",
    "Sistemas Operativos",
    "Inteligencia Artificial",
    "Matemáticas Discretas",
    "Cálculo Diferencial",
    "Probabilidad",
    "Arquitectura de Software",
    "Ingeniería de Software",
    "Compiladores",
    "Gráficos por Computador",
    "Teoría de Lenguajes",
    "Análisis Numérico",
    "Investigación de Operaciones",
]

FRANJAS = [
    ("06:00", "08:00"),
    ("08:00", "10:00"),
    ("10:00", "12:00"),
    ("12:00", "14:00"),
    ("14:00", "16:00"),
    ("16:00", "18:00"),
]

SEMILLA = 42

CONFIGURACIONES = {
    "caso_pequeno": {
        "materias": 4,
        "grupos_por_materia": 1,
        "sesiones_semanales_opciones": [1, 2],
        "salones": 2,
        "capacidad_salon_min": 20,
        "capacidad_salon_max": 40,
        "estudiantes_min": 10,
        "estudiantes_max": 35,
    },
    "caso_mediano": {
        "materias": 10,
        "grupos_por_materia": 2,
        "sesiones_semanales_opciones": [1, 2],
        "salones": 4,
        "capacidad_salon_min": 20,
        "capacidad_salon_max": 45,
        "estudiantes_min": 10,
        "estudiantes_max": 40,
    },
    "caso_grande": {
        "materias": 25,
        "grupos_por_materia": 3,
        "sesiones_semanales_opciones": [2],
        "salones": 8,
        "capacidad_salon_min": 20,
        "capacidad_salon_max": 50,
        "estudiantes_min": 10,
        "estudiantes_max": 45,
    },
}

def generar_bloques():
    """
    Crea los 30 bloques del calendario: uno por cada (día, franja).
    Cada bloque tiene un UUID real y único.
    """
    bloques = []
    for dia in DIAS:
        for hora_inicio, hora_fin in FRANJAS:
            bloques.append({
                "id": str(uuid4()),
                "dia": dia,
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin,
            })
    return bloques


def generar_salones(cantidad, cap_min, cap_max):
    """Crea salones con id tipo '1-103', '7-209', '13-310', etc."""
    
    numeros_disponibles = [
        piso * 100 + decena
        for piso in (1, 2, 3)
        for decena in range(0, 10)
    ]

    ids_usados = set()
    salones = []

    while len(salones) < cantidad:
        bloque = random.randint(1, 14)
        numero = random.choice(numeros_disponibles)
        id_salon = f"{bloque}-{numero}"

        if id_salon in ids_usados:
            continue

        ids_usados.add(id_salon)
        salones.append({
            "id": id_salon,
            "capacidad": random.randint(cap_min, cap_max),
        })

    return salones


def generar_profesor(id_materia, bloques, indice):
    """
    Crea un profesor con preferencias aleatorias por cada bloque.
    Como cada bloque ya representa (día, franja), las preferencias
    pueden variar por día de forma natural.
    """
    preferencias = {
        b["id"]: random.choice([0, 1, 2])
        for b in bloques
    }
    return {
        "id": str(uuid4()),
        "nombre": f"Profesor_{indice:02d}",
        "id_materia": str(id_materia),
        "preferencias": preferencias,
    }


def generar_grupo(id_materia, cantidad_estudiantes, indice):
    """Crea un grupo asociado a una única materia."""
    return {
        "id": str(uuid4()),
        "nombre": f"G{indice:02d}",
        "cantidad_de_estudiantes": cantidad_estudiantes,
        "id_materia": str(id_materia),
    }


def generar_materia(profesor, grupos, sesiones_semanales, indice):
    """Crea una materia a partir de su profesor y sus grupos."""
    return {
        "id": str(profesor["id_materia"]),
        "nombre": NOMBRES_MATERIAS[(indice - 1) % len(NOMBRES_MATERIAS)],
        "id_profesor": str(profesor["id"]),
        "id_grupos": [str(g["id"]) for g in grupos],
        "sesiones_semanales": sesiones_semanales,
    }

def generar_caso(config):
    """Genera la estructura completa de un caso."""
    bloques = generar_bloques()

    salones = generar_salones(
        cantidad=config["salones"],
        cap_min=config["capacidad_salon_min"],
        cap_max=config["capacidad_salon_max"],
    )

    materias = []
    grupos = []
    profesores = []

    contador_grupos = 1
    for i in range(1, config["materias"] + 1):
        id_materia = uuid4()

        grupos_materia = []
        for _ in range(config["grupos_por_materia"]):
            grupo = generar_grupo(
                id_materia=id_materia,
                cantidad_estudiantes=random.randint(
                    config["estudiantes_min"],
                    config["estudiantes_max"],
                ),
                indice=contador_grupos,
            )
            grupos_materia.append(grupo)
            grupos.append(grupo)
            contador_grupos += 1

        profesor = generar_profesor(
            id_materia=id_materia,
            bloques=bloques,
            indice=i,
        )
        profesores.append(profesor)

        materia = generar_materia(
            profesor=profesor,
            grupos=grupos_materia,
            sesiones_semanales=random.choice(
                config["sesiones_semanales_opciones"]
            ),
            indice=i,
        )
        materias.append(materia)

    return {
        "calendario": {
            "bloques": bloques,
        },
        "salones": salones,
        "profesores": profesores,
        "materias": materias,
        "grupos": grupos,
    }

def escribir_json(ruta: Path, contenido: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(contenido, f, indent=2, ensure_ascii=False)


def main():
    random.seed(SEMILLA)

    raiz = Path(__file__).resolve().parent.parent
    carpeta_datos = raiz / "datos"

    for nombre, config in CONFIGURACIONES.items():
        caso = generar_caso(config)
        ruta = carpeta_datos / f"{nombre}.json"
        escribir_json(ruta, caso)

        total_sesiones = sum(
            len(m["id_grupos"]) * m["sesiones_semanales"]
            for m in caso["materias"]
        )

        print(f"{nombre}.json generado")
        print(f"   materias : {len(caso['materias'])}")
        print(f"   grupos   : {len(caso['grupos'])}")
        print(f"   salones  : {len(caso['salones'])}")
        print(f"   bloques  : {len(caso['calendario']['bloques'])}")
        print(f"   sesiones : {total_sesiones}")
        print()


if __name__ == "__main__":
    main()