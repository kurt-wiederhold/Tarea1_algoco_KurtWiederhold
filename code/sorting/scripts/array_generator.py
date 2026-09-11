# =============================================================================
#  INF-221 Algoritmos y Complejidad -- Semestre 2026-2
#  Tarea 1: «Más allá de la notación asintótica»
#  Autor: Kurt Wiederhold        Rol: 202473528-4
#
#  Archivo: code/sorting/scripts/array_generator.py
#
#  SCRIPT ENTREGADO CON EL MATERIAL DE LA TAREA (anexo A.1 del enunciado: «Los
#  programas que generan estos arreglos se encuentran en
#  code/sorting/scripts/array_generator.py»). El código que sigue a esta
#  cabecera es el original sin modificar; sólo se antepone este comentario de
#  documentación, como pide el punto (4) de la sección 2.1.
#
#  Qué genera: los 72 arreglos {n}_{t}_{d}_{m}.txt del anexo A.1, con
#    n in {10^1, 10^3, 10^5, 10^7}, t in {ascendente, descendente, aleatorio},
#    d in {D1 = {0..9}, D7 = {0..10^7}}, m in {a, b, c},
#  en data/array_input/, cada arreglo en una línea con valores separados por
#  espacio.
#
#  Cómo ejecutarlo: escribe en la ruta relativa "../data/array_input", de modo
#  que debe lanzarse DESDE el directorio scripts/ (es lo que hace `make data`).
#  No fija semilla aleatoria, así que cada ejecución produce un conjunto de
#  datos distinto de la misma distribución.
#
#  Referencias:
#   [1] Documentación de NumPy, numpy.random.choice y numpy.sort,
#       https://numpy.org/doc/stable/reference/random/generated/numpy.random.choice.html
# =============================================================================

import numpy as np
import os

def generar_arreglo(n, tipo, dominio):
    if dominio == "D1":
        valores = np.arange(10)
    elif dominio == "D7":
        valores = np.arange(10**7 + 1)
    else:
        raise ValueError("Dominio no reconocido")

    if tipo == "ascendente":
        return np.sort(np.random.choice(valores, n, replace=True))
    elif tipo == "descendente":
        return np.sort(np.random.choice(valores, n, replace=True))[::-1]
    elif tipo == "aleatorio":
        return np.random.choice(valores, n, replace=True)
    else:
        raise ValueError("Tipo de ordenamiento no reconocido")

def guardar_arreglo(nombre_archivo, arreglo):
    with open(os.path.join("../data", "array_input", nombre_archivo), "w") as f:
        f.write(" ".join(map(str, arreglo)))

def generar_archivos():
    N = [10**1, 10**3, 10**5, 10**7]
    T = ["ascendente", "descendente", "aleatorio"]
    D = ["D1", "D7"]
    M = ["a", "b", "c"]

    for n in N:
        for t in T:
            for d in D:
                for m in M:
                    nombre_archivo = f"{n}_{t}_{d}_{m}.txt"
                    arreglo = generar_arreglo(n, t, d)
                    guardar_arreglo(nombre_archivo, arreglo)
                    print(f"Generado: {nombre_archivo}")

if __name__ == "__main__":
    generar_archivos()
