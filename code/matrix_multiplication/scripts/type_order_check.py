#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 INF-221 Algoritmos y Complejidad -- Semestre 2026-2
 Tarea 1: «Más allá de la notación asintótica»
 Autor: Kurt Wiederhold        Rol: 202473528-4

 Archivo: code/matrix_multiplication/scripts/type_order_check.py

 EXPERIMENTO DE CONTROL: aísla el efecto del TIPO de matriz del efecto del
 ORDEN DE EJECUCIÓN.

 Motivación. Ni el método clásico ni el de Strassen inspeccionan los
 coeficientes, así que una matriz diagonal debe costar exactamente lo mismo que
 una densa del mismo tamaño. En la corrida principal
 (`matrix_multiplication_measurements.csv`) el método clásico con n = 1024
 muestra una dispersión de ~6 % entre los seis pares tipo/dominio, y los casos
 se procesan en orden alfabético (densa, diagonal, dispersa). Antes de atribuir
 esa dispersión al dato hay que descartar que sea del orden de ejecución: una
 corrida larga calienta el procesador y puede bajar la frecuencia de «boost»,
 penalizando los casos que se procesan al final.

 Lectura del resultado. Se comparan dos cosas por separado: (1) la dispersión
 RELATIVA entre tipos, que es lo que responde la pregunta, y (2) el nivel
 ABSOLUTO de los tiempos. En las mediciones entregadas (1) coincide con la
 corrida principal (~6 %), pero (2) no: los tres tiempos aislados son ~25 %
 más altos que los de la corrida principal. Ese desplazamiento afecta por
 igual a los tres tipos, así que no cambia la conclusión sobre la estructura
 de la matriz, pero muestra que el nivel absoluto de una medición de ~3 s
 depende del estado de la máquina (térmico, frecuencia, carga de fondo) en el
 momento de medir; el informe lo declara en lugar de ocultarlo.

 Diseño. Para separar ambas causas, cada tipo de matriz se mide en un PROCESO
 INDEPENDIENTE y siempre en PRIMERA POSICIÓN, sobre un directorio de entrada que
 contiene únicamente su propio caso (1024_{tipo}_D10_a). Si la dispersión
 desaparece, la diferencia observada en la corrida principal era del orden de
 ejecución; si se mantiene, era del dato.

 Salida: data/measurements/matrix_type_order_check.csv, con el mismo esquema que
 el CSV principal para que ambos sean directamente comparables. Este es el
 archivo que respalda el último párrafo de la sección de resultados del informe.

 Uso:
   python scripts/type_order_check.py
   python scripts/type_order_check.py --n 256 --reps 5

 Referencias:
  [1] McGeoch, C. C. «A Guide to Experimental Algorithmics», Cambridge
      University Press, 2012. Cap. 1 y 3 (control de variables ocultas en
      experimentos con algoritmos; el orden de las mediciones como factor).
  [2] Hales, D. «An Introduction to Replicability in Computer Science
      Research», 2017 (registro del dato crudo que respalda cada afirmación).
  [3] AMD, «AMD Ryzen Processor Boost Technology» (la frecuencia sostenida
      depende de la temperatura y del tiempo bajo carga).
===============================================================================
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)      # code/matrix_multiplication

BINARY = os.path.join(
    PROJECT_DIR,
    "matrix_multiplication.exe" if os.name == "nt" else "matrix_multiplication")
INPUT_DIR = os.path.join(PROJECT_DIR, "data", "matrix_input")
DEFAULT_OUT = os.path.join(PROJECT_DIR, "data", "measurements",
                           "matrix_type_order_check.csv")

TIPOS = ["densa", "diagonal", "dispersa"]


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Aisla el efecto del tipo de matriz del orden de ejecucion.")
    p.add_argument("--n", type=int, default=1024, help="dimension a medir")
    p.add_argument("--domain", default="D10", help="dominio de los coeficientes")
    p.add_argument("--sample", default="a", help="muestra aleatoria")
    p.add_argument("--reps", type=int, default=3, help="repeticiones por tipo")
    p.add_argument("--out", default=DEFAULT_OUT, help="CSV de salida")
    p.add_argument("--binary", default=BINARY, help="ruta del programa de mediciones")
    args = p.parse_args(argv)

    if not os.path.isfile(args.binary):
        sys.exit(f"Error: no existe el binario {args.binary}.\nCompile primero con `make`.")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    filas, cabecera = [], None

    for i, tipo in enumerate(TIPOS, 1):
        base = f"{args.n}_{tipo}_{args.domain}_{args.sample}"
        origen = [os.path.join(INPUT_DIR, f"{base}_{k}.txt") for k in (1, 2)]
        if not all(os.path.isfile(o) for o in origen):
            sys.exit(f"Error: faltan las matrices de {base}. Ejecute `make data`.")

        # Directorio temporal con UN solo caso: asi ese tipo es necesariamente
        # el primero (y unico) que mide el proceso.
        with tempfile.TemporaryDirectory(prefix="typecheck_") as tmp:
            for o in origen:
                shutil.copy2(o, tmp)
            csv_tmp = os.path.join(tmp, "medicion.csv")
            cmd = [args.binary, "--input-dir", tmp, "--no-output", "--quiet",
                   "--reps", str(args.reps), "--measurements", csv_tmp]
            print(f"[{i}/{len(TIPOS)}] {base} en su propio proceso...", flush=True)
            r = subprocess.run(cmd, cwd=PROJECT_DIR)
            if r.returncode != 0:
                sys.exit(f"Error: el programa devolvio codigo {r.returncode} para {tipo}.")
            with open(csv_tmp, newline="", encoding="utf-8") as fh:
                lector = csv.reader(fh)
                cab = next(lector)
                cabecera = cabecera or cab
                filas.extend(lector)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cabecera)
        w.writerows(filas)

    # Resumen por pantalla
    import statistics
    print()
    tiempos = {}
    idx_t, idx_alg, idx_ms = cabecera.index("type"), cabecera.index("algorithm"), \
        cabecera.index("time_ms")
    for tipo in TIPOS:
        v = [float(f[idx_ms]) for f in filas if f[idx_t] == tipo and f[idx_alg] == "naive"]
        if v:
            tiempos[tipo] = statistics.median(v)
            print(f"  naive {tipo:9} {tiempos[tipo]:9.1f} ms")
    if len(tiempos) > 1:
        disp = max(tiempos.values()) / min(tiempos.values())
        print(f"\n  dispersion entre tipos: {(disp-1)*100:.1f} %")
    print(f"  mediciones en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
