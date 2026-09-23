from uuid import UUID

from .models.grupo import Grupo
from .models.materia import Materia
from .models.profesor import Profesor
from .models.sesion import Sesion


def construir_indices(datos: dict, sesiones: list[Sesion]) -> dict:

    materias_por_id: dict[UUID, Materia] = {m.id: m for m in datos["materias"]}
    profesores_por_id: dict[UUID, Profesor] = {p.id: p for p in datos["profesores"]}
    grupos_por_id: dict[UUID, Grupo] = datos["grupos"]
    sesiones_por_id: dict[UUID, Sesion] = {s.id: s for s in sesiones}

    contexto_sesion: dict[UUID, dict] = {}
    for s in sesiones:
        materia = materias_por_id[s.id_materia]
        profesor = profesores_por_id[materia.id_profesor]
        grupo = grupos_por_id[s.id_grupo]
        contexto_sesion[s.id] = {
            "sesion": s,
            "materia": materia,
            "profesor": profesor,
            "grupo": grupo,
        }

    return {
        "materias_por_id": materias_por_id,
        "profesores_por_id": profesores_por_id,
        "grupos_por_id": grupos_por_id,
        "sesiones_por_id": sesiones_por_id,
        "contexto_sesion": contexto_sesion,
    }

if __name__ == "__main__":
    from .cargador import cargar_datos
    from .generar_sesiones import generar_sesiones

    for caso in ["caso_pequeno", "caso_mediano", "caso_grande"]:
        d = cargar_datos(f"datos/{caso}.json")
        sesiones = generar_sesiones(d["materias"], d["grupos"])
        idx = construir_indices(d, sesiones)
        print(f"{caso}: {len(idx['sesiones_por_id'])} sesiones indexadas")