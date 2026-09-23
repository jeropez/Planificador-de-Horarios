from uuid import uuid4

from .models.grupo import Grupo
from .models.materia import Materia
from .models.sesion import Sesion


def generar_sesiones(
    materias: list[Materia],
    grupos: dict,
) -> list[Sesion]:
    """
    Genera las sesiones que deben ser programadas.

    Se crea una sesión por cada grupo de una materia
    y por cada sesión semanal de dicha materia.
    """

    sesiones = []

    for materia in materias:
        for id_grupo in materia.id_grupos:
            grupo: Grupo = grupos[id_grupo]

            for _ in range(materia.sesiones_semanales):
                sesion = Sesion(
                    id=uuid4(),
                    id_materia=materia.id,
                    id_grupo=grupo.id
                )

                sesiones.append(sesion)

    return sesiones

if __name__ == "__main__":
    from src.cargador import cargar_datos

    for caso in ["caso_pequeno", "caso_mediano", "caso_grande"]:
        d = cargar_datos(f"datos/{caso}.json")
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        print(f"{caso}: {len(sesiones)} sesiones")