#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 INF-221 Algoritmos y Complejidad -- Semestre 2026-2
 Tarea 1: «Más allá de la notación asintótica»
 Autor: Kurt Wiederhold        Rol: 202473528-4

 Archivo: code/matrix_multiplication/scripts/stride_check.py

 EXPERIMENTO DE CONTROL: ¿el exponente medido del método clásico (p ≈ 3,5 en
 lugar de 3) se debe a que la matriz «deja de caber en caché», o a que n es
 una POTENCIA DE DOS?

 Motivación. El bucle interno del método clásico recorre B por columnas: dos
 accesos consecutivos distan 8·n bytes. Cuando n es potencia de dos ese salto
 es múltiplo de 4096 (para n ≥ 512) o de una fracción grande de la página, y
 TODOS los elementos de una columna caen en el mismo conjunto de la caché
 (L1d: 64 conjuntos de 64 B; con stride 8192 B el índice de conjunto es
 siempre el mismo). Con 8 o 12 vías, cada acceso es un fallo de caché aunque
 la matriz completa quepa de sobra en L2 o L3. Es el «aliasing» de conjuntos
 descrito en [1], sección 6.2.1, y en [2].

 Diseño. Se mide el método clásico (y Strassen, como referencia) sobre
 matrices densas D10 de dimensión n y n ± 3..40, es decir, tamaños vecinos
 que ocupan la MISMA memoria pero cuyo stride NO es potencia de dos:
   {250, 256, 260}, {500, 512, 520}, {1000, 1024, 1040}.
 Si el costo por operación t/n³ es parecido en los tres tamaños de cada grupo,
 la causa es la capacidad de la caché; si sólo la potencia de dos es lenta, la
 causa es el conflicto de conjuntos. Los datos se generan con el mismo
 generador del enunciado (matrix_generator.py) y se miden con el mismo
 programa principal, así que la metodología es idéntica a la corrida
 principal.

 Nota: Strassen rellena n hasta la siguiente potencia de dos, de modo que para
 n = 1000 o 1040 hace el mismo trabajo que para 1024 (o 2048): sus tiempos se
 registran por completitud, pero el análisis usa el método clásico.

 Salida: data/measurements/matrix_stride_check.csv, con el mismo esquema que
 el CSV principal. plot_generator.py produce a partir de él la figura
 matrix_stride_check.png y la tabla table_matrix_stride.tex.

 Uso:
   python scripts/stride_check.py
   python scripts/stride_check.py --sizes 1000 1024 1040 --reps 3

 Referencias:
  [1] Drepper, U. «What Every Programmer Should Know About Memory», 2007,
      secc. 3.3.2 (asociatividad) y 6.2.1 (multiplicación de matrices).
  [2] Intel, «Intel 64 and IA-32 Architectures Optimization Reference Manual»,
      secc. «Capacity Limits and Aliasing in Caches» (4K aliasing).
  [3] McGeoch, C. C. «A Guide to Experimental Algorithmics», CUP, 2012, cap. 3
      (experimentos de control para descartar explicaciones alternativas).
===============================================================================
"""

import argparse
import os
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)      # code/matrix_multiplication
sys.path.insert(0, SCRIPT_DIR)
from matrix_generator import generar_matriz, guardar_matriz  # noqa: E402

BINARY = os.path.join(
    PROJECT_DIR,
    "matrix_multiplication.exe" if os.name == "nt" else "matrix_multiplication")
DEFAULT_OUT = os.path.join(PROJECT_DIR, "data", "measurements",
                           "matrix_stride_check.csv")
DEFAULT_SIZES = [250, 256, 260, 500, 512, 520, 1000, 1024, 1040]


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Control: potencia de dos vs. tamanos vecinos en el metodo clasico.")
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES,
                   help="dimensiones a medir")
    p.add_argument("--reps", type=int, default=3, help="repeticiones por caso")
    p.add_argument("--domain", default="D10", help="dominio de los coeficientes")
    p.add_argument("--out", default=DEFAULT_OUT, help="CSV de salida")
    p.add_argument("--binary", default=BINARY, help="ruta del programa de mediciones")
    args = p.parse_args(argv)

    if not os.path.isfile(args.binary):
        sys.exit(f"Error: no existe el binario {args.binary}.\nCompile primero con `make`.")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Un unico directorio temporal con todos los casos; el programa principal
    # los ordena por n y los mide con la metodologia de siempre.
    with tempfile.TemporaryDirectory(prefix="stridecheck_") as tmp:
        for n in args.sizes:
            base = os.path.join(tmp, f"{n}_densa_{args.domain}_a")
            guardar_matriz(generar_matriz(n, "densa", args.domain), base + "_1.txt")
            guardar_matriz(generar_matriz(n, "densa", args.domain), base + "_2.txt")
            print(f"  generado n = {n}", flush=True)

        cmd = [args.binary, "--input-dir", tmp, "--no-output",
               "--reps", str(args.reps), "--measurements", args.out]
        print("Midiendo...", flush=True)
        r = subprocess.run(cmd, cwd=PROJECT_DIR)
        if r.returncode != 0:
            sys.exit(f"Error: el programa devolvio codigo {r.returncode}.")

    # Resumen por pantalla: costo por operacion del metodo clasico.
    import csv
    import statistics
    with open(args.out, newline="", encoding="utf-8") as fh:
        filas = [f for f in csv.DictReader(fh) if f["algorithm"] == "naive"]
    print()
    for n in sorted({int(f["n"]) for f in filas}):
        med = statistics.median(float(f["time_ms"]) for f in filas if int(f["n"]) == n)
        print(f"  naive n={n:5d}  {med:9.1f} ms   t/n^3 = {med * 1e6 / n ** 3:.3f} ns")
    print(f"  mediciones en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
