
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
│   ├── medicion_empirica.py 
│   ├── comparar_dp_backtracking.py  # DP vs backtracking + escalabilidad DP
│   └── benchmark_tecnicas.py        # tiempos de las 4 técnicas, S = 1..14
│
├── interfaz/
│   ├── index.html                   # abrir en el navegador
│   ├── estilos.css
│   ├── app.js
│   └── datos.js                     # generado por src.construir_interfaz
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
    ├── dinamica.py              # programación dinámica por bloques
    ├── generar_casos_multisesion.py  # casos con varias sesiones por materia
    ├── exportar_salidas.py      # JSON del horario de cada técnica
    ├── construir_interfaz.py    # empaqueta los datos de la interfaz
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

## Programación dinámica (`src/dinamica.py`)

### Por qué aplica

Las restricciones R3, R4 y R5 solo relacionan sesiones que caen en el **mismo bloque**, y R1 es individual. Dos sesiones en bloques distintos nunca entran en conflicto. Por eso el problema se resuelve bloque a bloque, recordando solo **qué** sesiones ya fueron programadas:

- **Estado:** `dp[b][mask]` = máxima preferencia acumulada usando los bloques `0..b-1`, donde `mask` es el conjunto de sesiones ya ubicadas.
- **Transición:** en el bloque `b` se elige un subconjunto `T` de sesiones pendientes que quepa en él: profesores distintos (R4), grupos distintos (R5) y un salón con capacidad suficiente para cada sesión (R1, R3). `dp[b+1][mask ∪ T] = max(dp[b][mask] + valor(b, T))`.
- **Respuesta:** `dp[B][todas]`, que garantiza R6.
- **Subproblemas solapados:** distintos órdenes de colocar las mismas sesiones llegan a la misma `mask`; la DP los resuelve una sola vez.

Para saber si `T` cabe en un bloque, se ordenan sesiones y salones de mayor a menor y se emparejan en ese orden (R1 es un umbral, así que basta). Los subconjuntos factibles se precalculan una sola vez, porque no dependen del bloque.

### Modelo restringido

La DP optimiza la **preferencia del profesor**, que es aditiva por (sesión, bloque). Los términos por pares del mismo grupo (misma franja, mismo salón, días distintos) y el uso global de salones **no son aditivos**: incluirlos exigiría guardar en el estado la franja, el salón y el día de cada sesión ya puesta, y el número de estados volvería a explotar. Por eso la solución es **óptima para R1–R6 + preferencia**, y `evaluar_calidad` se reporta solo como medida.

Como desempate se resta una penalización mínima (`1e-3`) por cada par de sesiones en el mismo bloque. Nunca cambia la preferencia óptima, pero favorece horarios que usan menos salones a la vez.

### Complejidad

- **Temporal:** cada máscara recorre los subconjuntos de su complemento, `O(3^S)` por bloque. **Total: `O(B · 3^S)`**, frente a `O(60^S · S²)` de la fuerza bruta.
- **Espacial:** `O(2^S)` para los subconjuntos factibles más `O(B · 2^S)` para los punteros de reconstrucción.

### Resultados: DP vs backtracking

```bash
python -m analisis.comparar_dp_backtracking
```

| Caso | S | DP preferencia | DP calidad | DP tiempo (s) | BT preferencia | BT calidad | BT tiempo (s) | BT nodos |
|---|---|---|---|---|---|---|---|---|
| caso_pequeno | 2 | 2.00 | 1.000 | 0.0002 | 2.00 | 1.000 | 0.0135 | 3 601 |
| caso_mediano | 3 | 3.00 | 1.000 | 0.0004 | 3.00 | 1.000 | 0.9230 | 208 921 |
| caso_grande | 4 | 4.00 | 1.000 | 0.0010 | 4.00 | 1.000 | 60.2851 | 11 912 161 |
| sintético (2 materias × 2 sesiones) | 4 | 4.00 | 0.800 | 0.0010 | 4.00 | 1.000 | 66.2271 | 11 515 381 |

- La DP alcanza siempre la **misma preferencia óptima** que backtracking, unas 60 000 veces más rápido en `S = 4`.
- En el caso sintético cada grupo tiene dos sesiones y los términos por pares sí cuentan: la DP no los optimiza y obtiene calidad 0.800 frente a 1.000. Es el costo del modelo restringido.

### Escalabilidad de la DP

| S | Estados explorados | Subconjuntos factibles | Tiempo (s) |
|---|---|---|---|
| 6 | 1 884 | 26 | 0.009 |
| 8 | 7 481 | 64 | 0.074 |
| 10 | 29 651 | 130 | 0.598 |
| 12 | 117 353 | 232 | 4.477 |
| 14 | 464 122 | 378 | 30.788 |

Cada 2 sesiones adicionales el tiempo se multiplica por unas 7–8 veces, cerca del factor `3² = 9` esperado. El límite práctico ronda `S ≈ 14`, frente a `S = 4` para la fuerza bruta.

---

## Casos multisesión y salidas por técnica

En los casos originales cada materia tiene una sola sesión, así que los términos por pares de la calidad no aportan y las cuatro técnicas empatan en 1.0. Para que se diferencien se agregaron casos con varias sesiones por materia, sin modificar los originales:

| Caso | Materias | Grupos | Sesiones por grupo | Salones | S |
|---|---|---|---|---|---|
| `caso_multi_pequeno` | 2 | 2 | 2 | 2 | 4 |
| `caso_multi_mediano` | 2 | 4 | 2 | 2 | 8 |
| `caso_multi_grande` | 4 | 4 | 3 | 3 | 12 |

```bash
python -m src.generar_casos_multisesion   # crea los 3 JSON en datos/ (semilla 2026)
python -m src.exportar_salidas            # horario de cada técnica en cada caso
python -m src.exportar_salidas caso_multi_grande   # solo los casos indicados
```

`exportar_salidas` escribe `datos/salidas/<caso>/<tecnica>.json` con las métricas, la lista de asignaciones legible (materia, profesor, grupo, día, franja, salón, preferencia) y el horario por salón. Fuerza bruta y backtracking se omiten cuando `S > 4`, porque no terminan en un tiempo razonable.

### Resultados (calidad · preferencia acumulada · tiempo)

| Caso | S | Fuerza bruta | Greedy | Backtracking | DP |
|---|---|---|---|---|---|
| `caso_multi_pequeno` | 4 | 1.000 · 4.0 · 112.7 s | 1.000 · 4.0 · 0.0008 s | 1.000 · 4.0 · 65.6 s | 0.600 · 4.0 · 0.0010 s |
| `caso_multi_mediano` | 8 | — | 0.963 · 7.0 · 0.0023 s | — | 0.700 · **8.0** · 0.043 s |
| `caso_multi_grande` | 12 | — | 0.938 · 9.5 · 0.0071 s | — | 0.733 · **12.0** · 3.60 s |

- **La DP maximiza la preferencia** (es óptima en ese objetivo y le gana a greedy por 1 y 2.5 puntos), pero **no optimiza los términos por pares**. Por eso su calidad completa es menor.
- **Greedy** optimiza la calidad completa paso a paso y aquí obtiene la mejor calidad entre las técnicas que escalan, aunque no garantiza el óptimo (ver `analisis/contraejemplo_greedy.py`).
- **Fuerza bruta y backtracking** dan el óptimo de la calidad completa, pero solo son viables hasta `S = 4`.

---

## Interfaz gráfica (`interfaz/`)

Página web con dos pestañas:

- **Horarios:** eliges un caso y una técnica, y ves sus métricas (calidad, preferencia, tiempo, salones, trabajo). El horario se puede ver como **semana** (días × franjas, coloreado por materia), como **tabla** ordenable con descarga en CSV, o en **Comparar técnicas**, que pone los horarios de las cuatro técnicas lado a lado y marca qué clases quedaron en otro día o franja. Se puede filtrar por día, materia, profesor, grupo, salón o texto. Al pasar el cursor sobre una clase se resaltan las demás de su grupo, y al hacer clic se abre su detalle.
- **Análisis:** resumen de cada técnica (complejidad temporal y espacial, optimalidad, límite práctico), gráficas de tiempo medido (escala log/lineal), trabajo realizado, complejidad teórica, calidad y preferencia por caso, calidad a medida que crece `S`, aceleración frente a la fuerza bruta, una calculadora que estima cuánto tardaría cada técnica con `S` sesiones y una tabla comparativa.

### Cómo abrirla

Abrir `interfaz/index.html` con doble clic en el navegador. Las gráficas usan Chart.js desde un CDN, así que necesitan conexión a internet.

### Cómo regenerar los datos

La página lee `interfaz/datos.js`, que se arma a partir de las salidas y del benchmark:

```bash
python -m src.exportar_salidas          # JSON de cada técnica en datos/salidas/ (~6 min)
python -m analisis.benchmark_tecnicas   # tiempos para S = 1..14 en datos/benchmark_tecnicas.json (~5 min)
python -m src.construir_interfaz        # empaqueta todo en interfaz/datos.js
```

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