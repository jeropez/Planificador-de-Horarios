
import sys
import time

import matplotlib.pyplot as plt

sys.path.insert(0, ".")  # para que encuentre la carpeta src (ejecutar desde la raíz del proyecto)

from src.cargador import cargar_datos
from src.generar_sesiones import generar_sesiones
from src.indices import construir_indices
from src.fuerza_bruta import fuerza_bruta

casos = ["exp_s1", "caso_pequeno", "caso_mediano", "caso_grande"]

# Aquí se guardan los resultados para la gráfica
lista_sesiones = []
lista_tiempos = []
lista_combinaciones = []

# Encabezado de la tabla
print(f"{'caso':<15}{'sesiones':>10}{'combinaciones':>16}{'tiempo':>12}")
print("-" * 53)

for caso in casos:
    # 1. Cargar los datos del caso
    datos = cargar_datos(f"datos/{caso}.json")
    sesiones = generar_sesiones(datos["materias"], datos["grupos"])
    indices = construir_indices(datos, sesiones)

    # 2. Medir cuánto tarda la fuerza bruta
    inicio = time.perf_counter()
    resultado = fuerza_bruta(sesiones, datos, indices)
    fin = time.perf_counter()
    tiempo = fin - inicio

    # 3. Mostrar una fila de la tabla
    combinaciones = resultado["combinaciones_probadas"]
    texto = f"{combinaciones:,}".replace(",", " ")
    print(f"{caso:<15}{len(sesiones):>10}{texto:>16}{tiempo:>10.4f} s", flush=True)

    # 4. Guardar los datos para la gráfica
    lista_sesiones.append(len(sesiones))
    lista_tiempos.append(tiempo)
    lista_combinaciones.append(combinaciones)

# ---------------- Gráfica ----------------
fig, ax1 = plt.subplots(figsize=(9, 6))

# Tiempo (eje izquierdo, escala logarítmica)
ax1.plot(lista_sesiones, lista_tiempos, "o-", color="tab:blue", label="Tiempo (s)")
ax1.set_xlabel("Número de sesiones")
ax1.set_ylabel("Tiempo (s)", color="tab:blue")
ax1.set_yscale("log")
ax1.set_xticks(lista_sesiones)
ax1.grid(True, which="both", linestyle="--", alpha=0.4)

# Combinaciones probadas (eje derecho, escala logarítmica)
ax2 = ax1.twinx()
ax2.plot(lista_sesiones, lista_combinaciones, "s--", color="tab:red", label="Combinaciones probadas")
ax2.set_ylabel("Combinaciones probadas", color="tab:red")
ax2.set_yscale("log")

# Leyenda con las dos líneas
lineas = ax1.get_lines() + ax2.get_lines()
ax1.legend(lineas, [l.get_label() for l in lineas], loc="upper left")

plt.title("Fuerza bruta: tiempo vs número de sesiones")
plt.tight_layout()
plt.savefig("docs/grafica_tiempos.png", dpi=150)
print("\nGráfica guardada en docs/grafica_tiempos.png")