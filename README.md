# Planificador de Horarios

Proyecto de la asignatura **Análisis y Diseño de Algoritmos**.

Sistema que genera horarios académicos asignando clases de distintas materias a profesores, grupos de estudiantes, salones, días y bloques horarios, respetando restricciones obligatorias y buscando una solución de buena calidad según preferencias.

El problema se resuelve con **cinco técnicas** que se comparan entre sí:

| Técnica | Archivo | Idea |
|---|---|---|
| Fuerza bruta | `src/fuerza_bruta.py` | Prueba todas las combinaciones y se queda con la mejor. |
| Voraz (greedy) | `src/greedy.py` | Decide sesión por sesión la mejor opción local, sin retroceder. |
| Backtracking | `src/backtracking.py` | Recorre el árbol de decisiones descartando ramas inviables. |
| Programación dinámica | `src/dinamica.py` | Resuelve bloque a bloque reutilizando subproblemas. |
| Divide y vencerás | `src/divide_venceras.py` | Resuelve cada materia por separado y combina los horarios. |

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
│   ├── medicion_empirica.py         # tiempos de la fuerza bruta (S = 1..4)
│   ├── contraejemplo_greedy.py      # instancia donde greedy no es óptimo
│   ├── comparar_dp_backtracking.py  # DP vs backtracking + escalabilidad DP
│   ├── validar_divide_venceras.py   # divide y vencerás vs óptimo exhaustivo
│   └── benchmark_tecnicas.py        # tiempos de las 5 técnicas, S = 1..14
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
│   ├── caso_multi_pequeno.json      # S = 4  (varias sesiones por materia)
│   ├── caso_multi_mediano.json      # S = 8
│   ├── caso_multi_grande.json       # S = 12
│   ├── exp_s1.json                  # S = 1 sesión (para la gráfica)
│   ├── experimento_resultados.json  # resultados crudos del experimento
│   ├── benchmark_tecnicas.json      # resultados de analisis.benchmark_tecnicas
│   ├── salida_caso_pequeno.json     # ejemplo de salida generada
│   └── salidas/<caso>/<tecnica>.json  # horario de cada técnica en cada caso
│
├── docs/
│   ├── grafica_tiempos.png
│   ├── entrega_1.pdf
│   ├── entrega3_final.pdf           # documento final (entregas 1, 2 y 3)
│   ├── comparativa_tiempos.png      # tiempos de las 5 técnicas (src.comparativa)
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
    ├── generar_datos.py         # genera los JSON de entrada
    ├── generador_s1.py          # genera el caso S = 1
    ├── generar_casos_multisesion.py  # casos con varias sesiones por materia
    ├── cargador.py              # lee JSON y construye objetos
    ├── generar_sesiones.py      # crea las sesiones a programar
    ├── indices.py               # índices auxiliares (contexto_sesion)
    ├── validaciones.py          # restricciones duras R1–R5
    ├── calidad.py               # función de calidad (preferencias blandas)
    ├── fuerza_bruta.py          # técnica 1: fuerza bruta
    ├── greedy.py                # técnica 2: voraz
    ├── backtracking.py          # técnica 3: backtracking con poda
    ├── dinamica.py              # técnica 4: programación dinámica por bloques
    ├── divide_venceras.py       # técnica 5: divide y vencerás por materia
    ├── salida.py                # formato final por salón
    ├── comparativa.py           # comparativa final: n = 100 y 1000 + gráfica de tiempos
    ├── exportar_salidas.py      # JSON del horario de cada técnica
    ├── construir_interfaz.py    # empaqueta los datos de la interfaz
    └── experimento.py           # mide tiempos de la fuerza bruta y genera la gráfica
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
cargador.py           → objetos Python
    ↓
generar_sesiones.py   → lista de Sesion
    ↓
indices.py            → contexto_sesion (materia, profesor, grupo por sesión)
    ↓
fuerza_bruta.py │ greedy.py │ backtracking.py │ dinamica.py │ divide_venceras.py
                      → solución (lista de Asignacion) + métricas
    ↓
salida.py             → diccionario por salón
    ↓
JSON de salida
```

Las cinco técnicas reciben los mismos parámetros `(sesiones, datos, indices)` y devuelven un `dict` con al menos `solucion` y `calidad`, así que son intercambiables.

---

## Cómo ejecutar

Todos los comandos se corren desde la raíz del proyecto.

### 1. Generar los datos de entrada

```bash
python -m src.generar_datos
```

Genera `caso_pequeno.json`, `caso_mediano.json` y `caso_grande.json` en `datos/`.

```bash
python -m src.generador_s1                # caso S = 1 (para la gráfica)
python -m src.generar_casos_multisesion   # casos con varias sesiones por materia
```

### 2. Correr cada técnica sobre los tres casos originales

```bash
python -m src.fuerza_bruta    # ~2 min por caso_grande
python -m src.greedy
python -m src.backtracking    # ~1 min por caso_grande
python -m src.dinamica
python -m src.divide_venceras # corre también los casos multisesión
```

Cada una imprime tiempo, calidad, si la solución es completa y su contador de trabajo (combinaciones, candidatos, nodos o estados).

### 3. Experimentos y comparaciones

```bash
python -m src.experimento                    # fuerza bruta S = 1..4 + gráfica
python -m analisis.contraejemplo_greedy      # instancia donde greedy no es óptimo
python -m analisis.comparar_dp_backtracking  # DP vs backtracking
python -m analisis.validar_divide_venceras   # divide y vencerás vs óptimo exhaustivo
python -m analisis.benchmark_tecnicas        # las 5 técnicas, S = 1..14 (~5 min)
python -m analisis.benchmark_tecnicas divide_venceras  # solo esa técnica
python -m src.comparativa                    # n = 100 y 1000 + docs/comparativa_tiempos.png (~8 min)
```

`src.comparativa` mide greedy y divide y vencerás con n = 100 y n = 1000. Fuerza bruta, backtracking y programación dinámica no terminan con esos tamaños, así que su tiempo se estima a partir del mayor n medido y su fórmula de complejidad (con n = 100, la fuerza bruta tardaría unos 10²⁰⁸ años).

### 4. Exportar los horarios y abrir la interfaz

```bash
python -m src.exportar_salidas      # datos/salidas/<caso>/<tecnica>.json
python -m src.construir_interfaz    # interfaz/datos.js
```

Luego abrir `interfaz/index.html` en el navegador.

### 5. Generar la salida de una técnica en formato por salón

```bash
python -c "
import json
from src.cargador import cargar_datos
from src.generar_sesiones import generar_sesiones
from src.indices import construir_indices
from src.greedy import greedy
from src.salida import formatear_horario, imprimir_horario

d = cargar_datos('datos/caso_pequeno.json')
sesiones = generar_sesiones(d['materias'], d['grupos'])
idx = construir_indices(d, sesiones)

r = greedy(sesiones, d, idx)
horario = formatear_horario(r['solucion'], d, idx)
imprimir_horario(horario)

with open('datos/salida_caso_pequeno.json', 'w', encoding='utf-8') as f:
    json.dump(horario, f, indent=2, ensure_ascii=False)
"
```

Para usar otra técnica basta cambiar el import y la llamada (`fuerza_bruta`, `backtracking`, `dinamica` o `divide_venceras`).

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

## Notación

| Símbolo | Significado | Valor en los casos |
|---|---|---|
| `S` | Número de sesiones a programar | 1 – 14 |
| `B` | Bloques semanales (día × franja) | 30 |
| `A` | Salones | 2 – 3 |
| `B · A` | Opciones (bloque, salón) por sesión | 60 con 2 salones |

---

## Técnica 1: Fuerza bruta (`src/fuerza_bruta.py`)

### Estrategia

1. Genera **todas** las combinaciones del producto cartesiano `(bloque, salón)` para cada sesión, con `itertools.product`. No hay poda ni retroceso.
2. Para cada combinación, verifica R1 al construirla y luego R3, R4 y R5 (`_es_valida`).
3. A las combinaciones válidas les calcula la calidad con `evaluar_calidad`.
4. Devuelve la de mayor calidad.

Como revisa todo el espacio, **siempre encuentra el óptimo de la calidad completa**. Sirve como referencia para validar las demás técnicas.

### Complejidad temporal

- Opciones por sesión: `B · A`.
- Total de combinaciones: `(B · A)^S`.
- Por cada combinación: validar R1–R5 y calcular calidad cuesta `O(S²)`.
- **Complejidad total:** `O((B · A)^S · S²)`.

Con los datos actuales (`B · A = 60`): **`O(60^S · S²)`**. El término dominante es `60^S`, exponencial en el número de sesiones.

### Complejidad espacial

- Almacenar una solución: `O(S)`.
- Mejor solución guardada: `O(S)`.
- Sin recursión (iterativo con `itertools.product`).
- **Complejidad total:** `O(S)`.

### Resultados empíricos

| S | Combinaciones probadas | Tiempo (s) |
|---|---|---|
| 1 | 60 | 0.0007 |
| 2 | 3 600 | 0.0745 |
| 3 | 216 000 | 5.4712 |
| 4 | 12 960 000 | 438.2514 |

Cada incremento de `S` multiplica las combinaciones por exactamente **60**, confirmando el crecimiento `60^S`. El tiempo crece en el mismo orden de magnitud.

La gráfica en `docs/complejidad_fuerza_bruta.png` muestra ambos ejes en escala logarítmica, donde `60^S` aparece como una recta. (En la medición más reciente, `analisis.benchmark_tecnicas`, S = 4 tardó 117 s; la diferencia con la tabla se debe a la máquina y a la versión del código.)

---

## Técnica 2: Voraz / greedy (`src/greedy.py`)

### Estrategia

Toma dos decisiones locales, ambas **irrevocables** (nunca deshace una asignación):

1. **¿Qué sesión asigno ahora?** La **más restringida**: la que tiene menos opciones `(bloque, salón)` factibles con el tablero vacío. Desempate: el grupo más grande primero, porque necesita los salones de mayor capacidad. El orden se calcula una sola vez al inicio.
2. **¿Dónde la asigno?** Entre las opciones que cumplen R1, R3, R4 y R5, la que **maximiza la calidad parcial**, calculada con la misma `evaluar_calidad` que usa la fuerza bruta. Así las dos técnicas optimizan exactamente el mismo objetivo. Desempates: menor capacidad desperdiciada (best-fit) y, por último, el orden original de bloques y salones, para que sea determinista.

Los conflictos se revisan con tres conjuntos de ocupación — `(profesor, bloque)`, `(grupo, bloque)` y `(salón, bloque)` — así que cada verificación cuesta `O(1)`.

Si una sesión se queda sin opciones factibles, queda **sin asignar** (R6 se incumple) y se reporta en `no_asignadas`.

### ¿Es óptimo?

**No.** Una decisión que se ve bien ahora puede bloquear una mejor más adelante. `analisis/contraejemplo_greedy.py` compara greedy contra un óptimo exhaustivo en 3 000 instancias pequeñas y reporta la peor brecha encontrada:

| | Calidad |
|---|---|
| Greedy | 0.4875 |
| Óptimo | 0.9625 |

(2 salones de capacidad 40 y 20, 3 grupos de 35, 35 y 25 estudiantes, 4 bloques.) Greedy completa el horario, pero sus primeras decisiones lo obligan a separar las sesiones del mismo grupo y a usar más salones.

### Complejidad temporal

- **Orden inicial:** calcular las opciones de cada sesión cuesta `O(S · B · A)` y ordenar `O(S log S)`.
- **Bucle principal:** para cada una de las `S` sesiones se recorren hasta `B · A` opciones, y cada candidata se evalúa con `evaluar_calidad` sobre la solución parcial, que cuesta `O(S²)` por los pares del mismo grupo.
- **Complejidad total:** `O(S · B · A · S²) = O(S³ · B · A)`.

Es **polinomial**: con S = 14 tarda unos 6 ms.

### Complejidad espacial

- Conjuntos de ocupación y solución: `O(S)`.
- Lista de opciones de la sesión actual: `O(B · A)`.
- **Complejidad total:** `O(S + B · A)`.

### Resultados empíricos (`analisis.benchmark_tecnicas`)

| S | Candidatos evaluados | Tiempo | Calidad |
|---|---|---|---|
| 2 | 118 | 0.3 ms | 1.000 |
| 4 | 232 | 0.9 ms | 0.963 |
| 8 | 448 | 2.4 ms | 0.981 |
| 12 | 648 | 4.2 ms | 0.988 |
| 14 | 742 | 5.7 ms | 0.968 |

Los candidatos crecen casi linealmente con `S` (cada sesión ve como máximo `B · A = 60` opciones), y la calidad se mantiene alta, aunque sin garantía de ser la óptima.

---

## Técnica 3: Backtracking con poda (`src/backtracking.py`)

### Estrategia

Exploración **en profundidad** del árbol de asignaciones, sesión por sesión. En cada nodo se asigna una sesión a un `(bloque, salón)`, se baja un nivel y, al volver, se **deshace** la asignación para probar la siguiente opción. La calidad se evalúa solo en las hojas (soluciones completas), igual que en la fuerza bruta.

### Podas implementadas

| Poda | Qué hace |
|---|---|
| **P1. Restricciones duras** | Solo se prueban opciones que cumplen R1, R3, R4 y R5 en el estado actual, revisadas con conjuntos de ocupación en `O(1)`. |
| **P3. Forward checking** | Antes de bajar a una rama, comprueba que cada sesión pendiente siga teniendo al menos una opción factible. Si alguna se queda sin opciones, la rama se descarta. |
| **P4. Ordenamiento dinámico (MRV)** | En cada nivel elige primero la sesión con **menos opciones** en el estado actual (*Minimum Remaining Values*). Reduce el árbol sin perder optimalidad. |

No hay poda por calidad (*branch and bound*): por eso, con `buscar_optimo=True`, recorre todas las soluciones válidas.

### Modos

- `buscar_optimo=True`: recorre todo el árbol podado y devuelve la **mejor** solución. Encuentra el óptimo de la calidad completa, igual que la fuerza bruta.
- `buscar_optimo=False`: se detiene en la **primera** solución válida. Es mucho más rápido, pero sin garantía de calidad.

### Complejidad temporal

- **Nodos del árbol:** en el peor caso cada sesión puede ir a cualquiera de las `B · A` opciones, así que hay `O((B · A)^S)` nodos.
- **Costo por nodo:** MRV y forward checking recalculan las opciones de las sesiones pendientes, `O(S · B · A)`; en las hojas, `evaluar_calidad` cuesta `O(S²)`.
- **Complejidad total (peor caso):** `O((B · A)^S · S · B · A)`.

Las podas no cambian la cota del peor caso, pero sí el trabajo real: depende de cuántas ramas se descarten.

### Complejidad espacial

- Profundidad de la recursión: `S`.
- Cada nivel guarda su lista de opciones `O(B · A)` y la lista de pendientes `O(S)`.
- **Complejidad total:** `O(S · (B · A + S))`.

### Resultados empíricos

| S | Nodos explorados | Combinaciones de fuerza bruta | Tiempo backtracking | Tiempo fuerza bruta |
|---|---|---|---|---|
| 2 | 3 541 | 3 600 | 0.015 s | 0.021 s |
| 3 | 205 381 | 216 000 | 1.00 s | 1.40 s |
| 4 | 11 515 381 | 12 960 000 | 66.7 s | 117.4 s |

- Con estos datos casi todas las combinaciones son válidas (hay 30 bloques y pocas sesiones), así que la poda descarta poco: el backtracking explora alrededor del **89 %** de las combinaciones de la fuerza bruta. En `caso_grande` el forward checking nunca llegó a cortar una rama (`podas_aplicadas = 0`).
- Aun así es **1.8 veces más rápido**, porque valida cada restricción en `O(1)` al asignar, en lugar de revisar la combinación completa.
- La poda rinde mucho más cuando el problema está **ajustado** (pocos salones o bloques para muchas sesiones): ahí el forward checking descarta ramas enteras desde los primeros niveles.

---

## Técnica 4: Programación dinámica (`src/dinamica.py`)

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

## Técnica 5: Divide y vencerás por materia (`src/divide_venceras.py`)

### Por qué se puede dividir

Cada profesor enseña una sola materia (R7) y cada grupo ve una sola materia. Por eso dos sesiones de **materias distintas**:

- nunca comparten profesor (R4 no las relaciona),
- nunca comparten grupo (R5 no las relaciona), y
- nunca forman un par en la calidad (los pares son siempre del mismo grupo).

Lo único que las relaciona es **R3** (dos clases no pueden estar en el mismo salón y bloque) y el término global de **uso de salones**. Dividir el calendario en mitades de tiempo no sirve: habría que decidir antes qué sesiones van a cada mitad (2^S formas) y "días distintos" relaciona sesiones de mitades diferentes.

### Estrategia

1. **Dividir:** separar las sesiones por materia.
2. **Vencer:** resolver cada materia de forma exacta. Todas sus sesiones comparten profesor, así que van en bloques distintos y nunca chocan entre sí por salón. Por eso:
   - lo mejor para "mismo salón" es dejar cada grupo en un único salón, y
   - solo hay que escoger **qué bloques** usa cada grupo. Las sesiones de un grupo son intercambiables, así que son combinaciones `C(B, s)` y no permutaciones.

   El puntaje de cada elección es exactamente la parte de `evaluar_calidad` que depende de esa materia (preferencia y pares de misma franja, mismo salón y días distintos), con los mismos pesos y denominadores globales. Con ramificación y poda se guardan las **K = 50 mejores alternativas** por materia.
3. **Combinar:** se unen recursivamente mitades del conjunto de materias. En cada unión:
   - **Reparación:** si en algún bloque hay más clases de las que caben en los salones (R1, R3), se cambia una materia implicada a su siguiente alternativa, la que menos puntaje pierde.
   - **Ajuste de salones:** como el uso de salones es global, ninguna materia lo ve por separado. Si cambiar una materia a otra alternativa reduce las clases simultáneas lo suficiente para que la calidad total suba, se hace el cambio.
4. **Salones:** al final cada grupo intenta quedarse en un solo salón, prefiriendo los salones ya usados.

### Certificado de optimalidad

Como las materias no dependen entre sí, la suma de los mejores puntajes de cada materia más el máximo del uso de salones (un solo salón) es una **cota superior** de la calidad. Si la solución alcanza esa cota, es **óptima global**, y el algoritmo lo reporta en `optimo_garantizado`. Es la única técnica que puede certificar el óptimo sin explorar todo el espacio.

### Complejidad

Con `M` materias de `s` sesiones cada una (`S = M · s`):

- **Vencer:** `O(M · C(B, s) · s²)`. Con `s = 2`, cada materia evalúa `C(30, 2) = 435` combinaciones.
- **Combinar:** `log M` niveles de recursión. En cada uno se revisan los choques de los bloques en `O(S)` y cada reparación o ajuste prueba hasta `K` alternativas por materia.
- **Espacial:** `O(M · K · s)` para las alternativas guardadas.

El exponente pasa de `S` (todas las sesiones, en la fuerza bruta) a `s` (las sesiones de una materia).

### Validación (`analisis/validar_divide_venceras.py`)

Se comparó contra el óptimo exhaustivo en 717 instancias pequeñas con solución conocida:

| Resultado | Instancias |
|---|---|
| Igual al óptimo | 686 (95.7 %) |
| Por debajo del óptimo | 30 |
| Incompleta (no ubicó todas las sesiones) | 1 |
| Soluciones inválidas (R1, R3–R5) | **0** |
| Óptimo certificado | 481 |
| Certificados erróneos | **0** |

### Resultados

| Caso | S | Calidad | ¿Óptimo certificado? | Reparaciones | Ajustes de salones | Combinaciones | Tiempo |
|---|---|---|---|---|---|---|---|
| caso_pequeno | 2 | 1.000 | Sí | 0 | 0 | 60 | 0.2 ms |
| caso_mediano | 3 | 1.000 | Sí | 0 | 0 | 90 | 0.2 ms |
| caso_grande | 4 | 1.000 | Sí | 0 | 0 | 120 | 0.2 ms |
| caso_multi_pequeno | 4 | 1.000 | Sí | 0 | 0 | 870 | 0.7 ms |
| caso_multi_mediano | 8 | 1.000 | Sí | 0 | 1 | 1 740 | 1.8 ms |
| caso_multi_grande | 12 | 0.9625 | Sí | 0 | 2 | 16 240 | 16 ms |

En `caso_multi_grande` (S = 12) alcanza su cota superior, así que **es el óptimo global** en un tamaño donde la fuerza bruta necesitaría `90^12 ≈ 10^23` combinaciones. En el benchmark (S = 1..14) obtiene una calidad entre 0.95 y 1.00 en menos de 9 ms, por encima de greedy en todos los tamaños.

---

## Comparación de las cinco técnicas

| | Fuerza bruta | Greedy | Backtracking | Programación dinámica | Divide y vencerás |
|---|---|---|---|---|---|
| Complejidad temporal | `O((B·A)^S · S²)` | `O(S³ · B · A)` | `O((B·A)^S · S·B·A)` peor caso | `O(B · 3^S)` | `O(M · C(B, s) · s²)` + combinar |
| Complejidad espacial | `O(S)` | `O(S + B·A)` | `O(S · (B·A + S))` | `O(B · 2^S)` | `O(M · K · s)` |
| Qué optimiza | Calidad completa | Calidad completa (decisión local) | Calidad completa | Preferencia (R1–R6) | Calidad completa (exacta por materia) |
| ¿Garantiza el óptimo? | Sí | No | Sí | Sí, en preferencia | Lo certifica cuando alcanza la cota |
| ¿Retrocede? | No (lo prueba todo) | No | Sí | No (reutiliza subproblemas) | Solo al combinar |
| Tiempo con S = 4 | 117.4 s | 0.9 ms | 66.7 s | 1.0 ms | 0.6 ms |
| Límite práctico | S ≤ 4 | Cientos de sesiones | S ≤ 4 (modo óptimo) | S ≈ 14 | s ≲ 4 sesiones por materia |

Tiempos de `analisis.benchmark_tecnicas` (2 salones, materias de 2 sesiones). La interfaz gráfica muestra estas mismas comparaciones en la pestaña **Análisis**.

---

## Casos multisesión y salidas por técnica

En los casos originales cada materia tiene una sola sesión, así que los términos por pares de la calidad no aportan y todas las técnicas empatan en 1.0. Para que se diferencien se agregaron casos con varias sesiones por materia, sin modificar los originales:

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

| Caso | S | Fuerza bruta | Greedy | Backtracking | DP | Divide y vencerás |
|---|---|---|---|---|---|---|
| `caso_multi_pequeno` | 4 | 1.000 · 4.0 · 112.7 s | 1.000 · 4.0 · 0.0008 s | 1.000 · 4.0 · 65.6 s | 0.600 · 4.0 · 0.0010 s | 1.000 · 4.0 · 0.0007 s |
| `caso_multi_mediano` | 8 | — | 0.963 · 7.0 · 0.0023 s | — | 0.700 · **8.0** · 0.043 s | **1.000** · 7.0 · 0.0018 s |
| `caso_multi_grande` | 12 | — | 0.938 · 9.5 · 0.0071 s | — | 0.733 · **12.0** · 3.60 s | **0.963** · 10.5 · 0.016 s |

- **Divide y vencerás** obtiene la mejor calidad completa en todos los casos, en milisegundos, y en los tres casos certifica que es el óptimo global.
- **La DP maximiza la preferencia** (es óptima en ese objetivo), pero **no optimiza los términos por pares**. Por eso su calidad completa es menor.
- **Greedy** optimiza la calidad completa paso a paso y queda cerca, pero no garantiza el óptimo (ver `analisis/contraejemplo_greedy.py`).
- **Fuerza bruta y backtracking** dan el óptimo de la calidad completa, pero solo son viables hasta `S = 4`.

---

## Interfaz gráfica (`interfaz/`)

Página web con dos pestañas:

- **Horarios:** eliges un caso y una técnica, y ves sus métricas (calidad, preferencia, tiempo, salones, trabajo). El horario se puede ver como **semana** (días × franjas, coloreado por materia), como **tabla** ordenable con descarga en CSV, o en **Comparar técnicas**, que pone los horarios de las cinco técnicas lado a lado y marca qué clases quedaron en otro día o franja. Se puede filtrar por día, materia, profesor, grupo, salón o texto. Al pasar el cursor sobre una clase se resaltan las demás de su grupo, y al hacer clic se abre su detalle.
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

- **Fuerza bruta y backtracking** (en modo óptimo) son inviables para `S > 4`: con `S = 4` ya tardan entre 1 y 2 minutos, y cada sesión adicional multiplica el trabajo por 60.
- **Greedy** es rápido pero no garantiza el óptimo, y si una decisión temprana bloquea una sesión, puede dejarla sin asignar (incumple R6) porque no retrocede.
- **El backtracking no poda por calidad** (*branch and bound*), solo por factibilidad. Con datos holgados como los actuales, la poda descarta poco.
- **La programación dinámica** solo es exacta para el modelo restringido (R1–R6 + preferencia); no optimiza los términos por pares de la calidad. Su memoria crece como `2^S`, así que el límite práctico ronda `S ≈ 14`.
- **Divide y vencerás** depende de que las materias sean pequeñas: si una materia tiene muchas sesiones (por ejemplo 4 grupos × 3 sesiones), su subproblema vuelve a ser grande. Cuando hay pocos salones para muchas clases simultáneas, las reparaciones al combinar pueden alejarla del óptimo o, en casos muy ajustados, dejar sesiones sin ubicar.
- La función de calidad prioriza el uso eficiente de salones, lo que puede concentrar varias clases en el mismo salón.

---

## Tecnologías

- Python 3.10+ (usa `dict[UUID, int]`, `int | None`, etc.).
- `matplotlib` para la gráfica de complejidad.
- HTML, CSS y JavaScript, con Chart.js desde CDN, para la interfaz gráfica.
- Sin dependencias adicionales.
