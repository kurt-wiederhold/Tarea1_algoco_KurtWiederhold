#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 INF-221 Algoritmos y Complejidad -- Semestre 2026-2
 Tarea 1: «Más allá de la notación asintótica»
 Autor: Kurt Wiederhold        Rol: 202473528-4

 Archivo: code/matrix_multiplication/scripts/cutoff_sweep.py

 Barrido del UMBRAL DE CORTE de Strassen: ejecuta el programa principal una vez
 por cada umbral y acumula todas las mediciones en un mismo CSV
 (data/measurements/strassen_cutoff_sweep.csv), que después grafica
 plot_generator.py.

 Motivación: Strassen realiza 7 multiplicaciones de bloques en lugar de 8, pero
 paga 18 sumas de bloques y una asignación de memoria por nivel de recursión.
 Con umbral 1 (recursión pura hasta bloques de 1x1) ese sobrecosto domina por
 completo y el algoritmo resulta mucho más lento que el clásico pese a tener
 mejor exponente asintótico. El barrido permite medir dónde está el punto de
 equilibrio en esta máquina en lugar de suponerlo, que es justamente el tipo de
 pregunta que la notación asintótica no responde.

 Este script existe además por una razón práctica: el objetivo `make cutoff`
 necesita un bucle, y un bucle escrito en sintaxis de shell POSIX no funciona
 cuando GNU make usa cmd.exe en Windows. Orquestarlo desde Python hace que el
 objetivo se comporte igual en ambos sistemas.

 Uso:
   python scripts/cutoff_sweep.py
   python scripts/cutoff_sweep.py --cutoffs 1 8 64 --max-n 256

 Referencias:
  [1] Huss-Lederman, S. et al. «Implementation of Strassen's Algorithm for
      Matrix Multiplication», Proc. ACM/IEEE Supercomputing 96.
      doi:10.1145/369028.369096 (existencia de un umbral de corte óptimo y
      necesidad de determinarlo empíricamente en cada máquina).
  [2] Cormen, T. et al. «Introduction to Algorithms», 3rd ed., Sección 4.2.
  [3] McGeoch, C. C. «A Guide to Experimental Algorithmics», CUP, 2012, Cap. 3
      (barridos de parámetros como diseño experimental).
  [4] Documentación de Python, módulo subprocess,
      https://docs.python.org/3/library/subprocess.html
===============================================================================
"""

import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)      # code/matrix_multiplication

BINARY = os.path.join(
    PROJECT_DIR,
    "matrix_multiplication.exe" if os.name == "nt" else "matrix_multiplication")

DEFAULT_CUTOFFS = [1, 2, 4, 8, 16, 32, 64, 128, 256]
DEFAULT_OUT = os.path.join(PROJECT_DIR, "data", "measurements",
                           "strassen_cutoff_sweep.csv")


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Barrido del umbral de corte de Strassen.")
    p.add_argument("--cutoffs", type=int, nargs="+", default=DEFAULT_CUTOFFS,
                   help="umbrales a medir")
    p.add_argument("--max-n", type=int, default=256,
                   help="dimension maxima incluida en el barrido")
    p.add_argument("--out", default=DEFAULT_OUT, help="CSV de salida")
    p.add_argument("--binary", default=BINARY,
                   help="ruta del programa de mediciones")
    args = p.parse_args(argv)

    if not os.path.isfile(args.binary):
        sys.exit(f"Error: no existe el binario {args.binary}.\n"
                 f"Compile primero con `make`.")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    for i, cutoff in enumerate(args.cutoffs):
        cmd = [args.binary,
               "--cutoff", str(cutoff),
               "--max-n", str(args.max_n),
               "--no-output", "--quiet",
               "--measurements", args.out]
        # La primera corrida crea el CSV con su encabezado; las siguientes lo
        # amplian con --append.
        if i > 0:
            cmd.append("--append")

        print(f"[{i + 1}/{len(args.cutoffs)}] umbral = {cutoff} ...", flush=True)
        result = subprocess.run(cmd, cwd=PROJECT_DIR)
        if result.returncode != 0:
            sys.exit(f"Error: el programa devolvio codigo {result.returncode} "
                     f"con umbral {cutoff}.")

    print(f"\nBarrido completo. Mediciones en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
