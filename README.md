
---

# Planificador de Horarios

Proyecto de la asignatura **Análisis y Diseño de Algoritmos**.

Sistema que genera horarios académicos asignando clases de distintas materias a profesores, grupos de estudiantes, salones, días y bloques horarios, respetando restricciones obligatorias y buscando una solución de buena calidad según preferencias.

El algoritmo principal es una **solución de fuerza bruta** que explora todas las combinaciones posibles y selecciona la mejor según una función de calidad.

---

## Estructura del proyecto

```
Planificador-de-Horarios/
│
├── README.md
│
├── .gitignore
│
├── analisis/
│   └── medicion_empirica.py 
│
├── datos/
│   ├── caso_pequeno.json            # S = 2 sesiones
│   ├── caso_pequeno.txt  
│   ├── caso_mediano.json            # S = 3 sesiones
│   ├── caso_mediano.txt
│   ├── caso_grande.json             # S = 4 sesiones
│   ├── caso_grande.txt 
│   ├── exp_s1.json                  # S = 1 sesión (para la gráfica)
│   ├── experimento_resultados.json  # resultados crudos del experimento
│   └── salida_caso_pequeno.json     # ejemplo de salida generada
│
├── docs/
│   ├── grafica_tiempos.png
│   ├── entrega_1.pdf
│   └── complejidad_fuerza_bruta.png # gráfica tiempo vs tamaño
│
└── src/
    ├── __init__.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── asignacion.py
    │   ├── bloque.py
    │   ├── grupo.py
    │   ├── materia.py
    │   ├── profesor.py
    │   ├── salon.py
    │   └── sesion.py
    │
    ├── generador_datos.py       # genera los JSON de entrada
    ├── generador_exp_s1.py      # genera el caso S = 1
    ├── cargador.py              # lee JSON y construye objetos
    ├── generador_sesiones.py    # crea las sesiones a programar
    ├── indices.py               # índices auxiliares (contexto_sesion)
    ├── validadores.py           # restricciones duras R1–R5
    ├── calidad.py               # función de calidad (preferencias blandas)
    ├── fuerza_bruta.py          # algoritmo principal
    ├── salida.py                # formato final por salón
    └── experimento.py           # mide tiempos y genera la gráfica
```

---

## Modelos

Todos los modelos usan `dataclasses` y `UUID`. La relación conceptual es:

```
Profesor → Materia → Grupo → Sesion → Asignacion → Salon
```

| Modelo | Campos |
|---|---|
| `Profesor` | `id`, `nombre`, `id_materia`, `preferencias: dict[UUID, int]` |
| `Grupo` | `id`, `nombre`, `cantidad_de_estudiantes`, `id_materia` |
| `Materia` | `id`, `nombre`, `id_profesor`, `id_grupos`, `sesiones_semanales` |
| `Salon` | `id` (str, ej. `14-103`), `capacidad` |
| `Bloque` | `id`, `dia`, `hora_inicio`, `hora_fin` |
| `Sesion` | `id`, `id_materia`, `id_grupo` |
| `Asignacion` | `id_sesion`, `id_salon`, `id_bloque` |

**Notas:**
- Cada profesor enseña **una sola** materia (R7).
- Cada grupo ve **una sola** materia.
- Un `Bloque` representa un día + una franja horaria concreta (ej. "martes 16:00–18:00"). Por eso hay 5 días × 6 franjas = **30 bloques**.
- `Asignacion` no incluye `dia` porque el día ya está dentro del `Bloque`.

---

## Calendario

- 5 días: lunes a viernes.
- 6 franjas de 2 horas: 06–08, 08–10, 10–12, 12–14, 14–16, 16–18.
- Total: **30 bloques semanales**.

---

## Restricciones duras (R1–R7)

| Código | Restricción |
|---|---|
| R1 | `capacidad_salon >= cantidad_estudiantes` |
| R2 | El salón debe estar disponible para el día y bloque escogidos |
| R3 | Un salón no puede tener dos clases simultáneamente |
| R4 | Un profesor no puede impartir dos clases simultáneamente |
| R5 | Un grupo no puede recibir dos clases simultáneamente |
| R6 | Todas las sesiones deben quedar programadas |
| R7 | Cada profesor enseña una sola materia |

R2 se garantiza mediante R3: si el salón está libre, está disponible. La ocupación se determina dinámicamente a partir de las asignaciones existentes.

---

## Preferencias blandas (calidad)

La calidad se representa con un valor normalizado `F ∈ [0, 1]`. Componentes:

| Componente | Peso | Descripción |
|---|---|---|
| Preferencia del profesor | 0.30 | `0/1/2` → `0.0/0.5/1.0`, promedio sobre sesiones |
| Misma franja | 0.20 | Pares del mismo grupo en la misma franja horaria |
| Mismo salón | 0.20 | Pares del mismo grupo en el mismo salón |
| Días distintos | 0.20 | Pares del mismo grupo en días diferentes |
| Uso de salones | 0.10 | `1 / salones_distintos_usados` |

Las preferencias **no son obligatorias**. Si no existe solución que las satisfaga, se devuelve la mejor solución válida según R1–R5.

---

## Flujo del sistema

```
JSON de entrada
    ↓
cargador.py          → objetos Python
    ↓
generador_sesiones.py → lista de Sesion
    ↓
indices.py           → contexto_sesion (materia, profesor, grupo por sesión)
    ↓
fuerza_bruta.py      → mejor solución (lista de Asignacion)
    ↓
salida.py            → diccionario por salón
    ↓
JSON de salida
```

---

## Cómo ejecutar

### 1. Generar los datos de entrada

```bash
python -m src.generador_datos
```

Genera `caso_pequeno.json`, `caso_mediano.json` y `caso_grande.json` en `datos/`.

### 2. Generar el caso S = 1 (para la gráfica)

```bash
python -m src.generador_exp_s1
```

### 3. Correr la fuerza bruta sobre los tres casos

```bash
python -m src.fuerza_bruta
```

Imprime tiempo, combinaciones probadas, calidad y si encontró solución.

### 4. Correr el experimento y generar la gráfica

```bash
python -m src.experimento
```

- Corre la fuerza bruta sobre S = 1, 2, 3, 4.
- Guarda resultados crudos en `datos/experimento_resultados.json`.
- Genera la gráfica en `docs/complejidad_fuerza_bruta.png`.

**Advertencia:** el caso S = 4 tarda varios minutos (~7 min en total).

### 5. Generar la salida en formato por salón

```bash
python -c "
import json
from src.cargador import cargar_datos
from src.generador_sesiones import generar_sesiones
from src.indices import construir_indices
from src.fuerza_bruta import fuerza_bruta
from src.salida import formatear_horario, imprimir_horario

d = cargar_datos('datos/caso_pequeno.json')
sesiones = generar_sesiones(d['materias'], d['grupos'])
idx = construir_indices(d, sesiones)

r = fuerza_bruta(sesiones, d, idx)
horario = formatear_horario(r['solucion'], d, idx)
imprimir_horario(horario)

with open('datos/salida_caso_pequeno.json', 'w', encoding='utf-8') as f:
    json.dump(horario, f, indent=2, ensure_ascii=False)
"
```

---

## Formato de la salida

Diccionario indexado por salón. Cada salón tiene 5 listas (una por día). Cada día tiene 6 posiciones (una por franja). Cada posición es una tupla `(materia, profesor, grupo, franja)` o `(null, null, null, null)` si está libre.

```json
{
  "11-103": [
    [
      [null, null, null, null],
      ["Cálculo en Varias Variables", "Profesor_01", "G01", "08:00-10:00"],
      [null, null, null, null],
      [null, null, null, null],
      [null, null, null, null],
      [null, null, null, null]
    ],
    "... (martes, miércoles, jueves, viernes)"
  ]
}
```

---

## Análisis de complejidad

### Temporal

La fuerza bruta genera el producto cartesiano de `(bloque, salón)` para cada sesión:

- Opciones por sesión: `B · A`, donde `B` = bloques (30) y `A` = salones.
- Total de combinaciones: `(B · A)^S`.
- Por cada combinación: validar R1–R5 y calcular calidad cuesta `O(S²)`.
- **Complejidad total:** `O((B · A)^S · S²)`.

Con los datos actuales (`B · A = 60`): **`O(60^S · S²)`**.

El término dominante es `60^S`, exponencial en el número de sesiones.

### Espacial

- Almacenar una solución: `O(S)`.
- Mejor solución guardada: `O(S)`.
- Sin recursión (iterativo con `itertools.product`).
- **Complejidad total:** `O(S)`.

---

## Resultados empíricos

| S | Combinaciones probadas | Tiempo (s) |
|---|---|---|
| 1 | 60 | 0.0007 |
| 2 | 3 600 | 0.0745 |
| 3 | 216 000 | 5.4712 |
| 4 | 12 960 000 | 438.2514 |

Cada incremento de `S` multiplica las combinaciones por exactamente **60**, confirmando el crecimiento `60^S`. El tiempo crece en el mismo orden de magnitud.

La gráfica en `docs/complejidad_fuerza_bruta.png` muestra ambos ejes en escala logarítmica, donde `60^S` aparece como una recta.

---

## Limitaciones

- La fuerza bruta pura es inviable para `S > 4` con los recursos actuales. El caso grande tarda más de 7 minutos.
- No se implementaron heurísticas ni poda (forward checking), porque el objetivo del ejercicio es analizar la complejidad de la fuerza bruta sin optimizaciones.
- La función de calidad prioriza el uso eficiente de salones, lo que puede concentrar varias clases en el mismo salón.

---

## Tecnologías

- Python 3.10+ (usa `dict[UUID, int]`, `int | None`, etc.).
- `matplotlib` para la gráfica de complejidad.
- Sin dependencias adicionales.
```

---