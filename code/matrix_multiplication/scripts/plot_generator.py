#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 INF-221 Algoritmos y Complejidad -- Semestre 2026-2
 Tarea 1: «Más allá de la notación asintótica»
 Autor: Kurt Wiederhold        Rol: 202473528-4

 Archivo: code/matrix_multiplication/scripts/plot_generator.py

 Lee data/measurements/matrix_multiplication_measurements.csv (producido por
 ./matrix_multiplication) y genera en data/plots/ los gráficos del mini-informe,
 además de las tablas LaTeX en data/measurements/.

 Igual que en el experimento de ordenamiento, TODA figura y TODA tabla del
 informe salen de este script; no hay ningún número escrito a mano.

 Estadístico usado: la MEDIANA sobre repeticiones y muestras {a,b,c}, robusta
 frente a los valores atípicos altos que introduce el sistema operativo.

 Figuras generadas:
   matrix_time_vs_n.png            tiempo vs n, un panel por tipo de matriz
   matrix_time_dense.png           caso denso con las cotas n^3 y n^2,807
   matrix_normalized.png           t/n^3 y t/n^2,807: constantes ocultas
   matrix_speedup.png              cociente naive/Strassen
   matrix_memory_vs_n.png          memoria auxiliar vs n
   matrix_type_effect.png          efecto del tipo de matriz
   matrix_cutoff_sweep.png         barrido del umbral de corte (si existe)
   matrix_stride_check.png         control: potencia de dos vs tamaños vecinos
                                   (si existe matrix_stride_check.csv)

 Tablas generadas (LaTeX):
   table_matrix_time.tex           tiempos medianos por algoritmo y n
   table_matrix_memory.tex         memoria auxiliar por algoritmo y n
   table_matrix_exponents.tex      exponente empírico ajustado por regresión
   table_matrix_stride.tex         costo por operación del clásico en n = 2^k
                                   y en sus vecinos (si existe el control)

 Macros generadas (LaTeX):
   numbers_matrix.tex              cada número que el informe cita en su prosa,
                                   calculado desde los CSV (véase la nota en
                                   code/sorting/scripts/plot_generator.py).

 Uso:  python scripts/plot_generator.py [--csv RUTA] [--out DIR]

 Referencias:
  [1] Documentación de Matplotlib, https://matplotlib.org/stable/
  [2] Strassen, V. «Gaussian elimination is not optimal», 1969 (exponente
      log2 7 = 2,807).
  [3] McGeoch, C. C. «A Guide to Experimental Algorithmics», CUP, 2012.
===============================================================================
"""

import argparse
import csv
import math
import os
import sys
from collections import defaultdict

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- Rutas resueltas respecto de la ubicación de ESTE archivo ----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)          # code/matrix_multiplication
DEFAULT_CSV = os.path.join(PROJECT_DIR, "data", "measurements",
                           "matrix_multiplication_measurements.csv")
SWEEP_CSV = os.path.join(PROJECT_DIR, "data", "measurements",
                         "strassen_cutoff_sweep.csv")
STRIDE_CSV = os.path.join(PROJECT_DIR, "data", "measurements",
                          "matrix_stride_check.csv")
TYPECHECK_CSV = os.path.join(PROJECT_DIR, "data", "measurements",
                             "matrix_type_order_check.csv")
DEFAULT_PLOTS = os.path.join(PROJECT_DIR, "data", "plots")
DEFAULT_TABLES = os.path.join(PROJECT_DIR, "data", "measurements")

# --- Presentación uniforme ---------------------------------------------------
ALGOS = ["naive", "strassen"]
ALGO_LABEL = {"naive": "Clásico (naive)", "strassen": "Strassen"}
ALGO_COLOR = {"naive": "#1f77b4", "strassen": "#d62728"}
ALGO_MARKER = {"naive": "o", "strassen": "s"}

TYPES = ["densa", "dispersa", "diagonal"]
DOMAINS = ["D0", "D10"]
DOMAIN_LABEL = {"D0": r"$D_0=\{0,1\}$", "D10": r"$D_{10}=\{0,\dots,9\}$"}

STRASSEN_EXP = math.log2(7)      # 2,807...

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.dpi": 160,
    "font.size": 9,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
    "legend.frameon": True,
    "legend.framealpha": 0.9,
})


# ---------------------------------------------------------------------------
def load(csv_path, required=True):
    if not os.path.isfile(csv_path):
        if required:
            sys.exit(f"Error: no existe {csv_path}\n"
                     f"Ejecute primero el programa de mediciones (make run).")
        return []
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({
                    "algorithm": r["algorithm"],
                    "n": int(r["n"]),
                    "type": r["type"],
                    "domain": r["domain"],
                    "sample": r["sample"],
                    "rep": int(r["rep"]),
                    "time_ms": float(r["time_ms"]),
                    "heap": int(r["peak_heap_bytes"]),
                    "cutoff": int(r.get("cutoff", 0) or 0),
                    "correct": int(r["correct"]),
                })
            except (KeyError, ValueError):
                continue
    if required and not rows:
        sys.exit(f"Error: {csv_path} no contiene mediciones legibles.")
    return rows


def aggregate(rows, keys, field="time_ms"):
    buckets = defaultdict(list)
    for r in rows:
        buckets[tuple(r[k] for k in keys)].append(r[field])
    out = {}
    for k, v in buckets.items():
        a = np.asarray(v, dtype=float)
        out[k] = (float(np.median(a)), float(np.percentile(a, 25)),
                  float(np.percentile(a, 75)), len(a))
    return out


def sizes_of(rows):
    return sorted({r["n"] for r in rows})


def fit_exponent(ns, ts):
    ns = np.asarray(ns, dtype=float)
    ts = np.asarray(ts, dtype=float)
    mask = (ns > 0) & (ts > 0)
    if mask.sum() < 2:
        return float("nan"), float("nan"), float("nan")
    x, y = np.log(ns[mask]), np.log(ts[mask])
    p, b = np.polyfit(x, y, 1)
    pred = p * x + b
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(p), float(math.exp(b)), r2


def tex_num(v, dec=2):
    """Número para LaTeX en convención española: coma decimal ({,}) y espacio
    fino como separador de miles (\\,). tex_num(2630.3, 0) -> '2\\,630'."""
    s = f"{float(v):,.{dec}f}"
    ent, _, frac = s.partition(".")
    ent = ent.replace(",", "\\,")
    return ent + ("{,}" + frac if dec > 0 else "")


def human_bytes(b):
    """Tamano legible con coma decimal (convencion en espanol)."""
    b = float(b)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if b < 1024 or unit == "GiB":
            texto = f"{b:.0f} {unit}" if unit == "B" else f"{b:.1f} {unit}"
            return texto.replace(".", ",")
        b /= 1024


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------
def fig_time_vs_n(rows, out_dir):
    agg = aggregate(rows, ["algorithm", "n", "type", "domain"])
    ns_all = sizes_of(rows)

    fig, axes = plt.subplots(len(DOMAINS), len(TYPES),
                             figsize=(11, 6.2), sharex=True, sharey=True)
    for i, dom in enumerate(DOMAINS):
        for j, typ in enumerate(TYPES):
            ax = axes[i][j]
            for algo in ALGOS:
                xs, ys, lo, hi = [], [], [], []
                for n in ns_all:
                    k = (algo, n, typ, dom)
                    if k in agg:
                        med, q1, q3, _ = agg[k]
                        xs.append(n); ys.append(med); lo.append(q1); hi.append(q3)
                if not xs:
                    continue
                ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=5,
                        color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.6)
                ax.fill_between(xs, lo, hi, color=ALGO_COLOR[algo], alpha=0.18,
                                linewidth=0)
            ax.set_xscale("log", base=2); ax.set_yscale("log")
            if i == 0:
                ax.set_title(f"Matriz {typ}", fontsize=10)
            if j == 0:
                ax.set_ylabel(f"{DOMAIN_LABEL[dom]}\ntiempo [ms]")
            if i == len(DOMAINS) - 1:
                ax.set_xlabel("n (dimensión)")

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("Tiempo de multiplicación en función de la dimensión n\n"
                 "(mediana de 3 muestras x repeticiones; banda = rango intercuartílico)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0.05, 1, 0.93])
    path = os.path.join(out_dir, "matrix_time_vs_n.png")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


def fig_time_dense(rows, out_dir):
    """Caso denso D10 con las dos cotas teóricas superpuestas."""
    sub = [r for r in rows if r["type"] == "densa" and r["domain"] == "D10"]
    if not sub:
        return None
    agg = aggregate(sub, ["algorithm", "n"])
    ns_all = sizes_of(sub)

    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for algo in ALGOS:
        xs = [n for n in ns_all if (algo, n) in agg]
        ys = [agg[(algo, n)][0] for n in xs]
        if not xs:
            continue
        ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=6,
                color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.8)

    anchor_n = max(n for n in ns_all if ("naive", n) in agg)
    anchor_t = agg[("naive", anchor_n)][0]
    xs = np.array(ns_all, dtype=float)
    ax.plot(xs, anchor_t * (xs / anchor_n) ** 3, "k--", lw=1.1,
            label=r"referencia $\Theta(n^{3})$")
    ax.plot(xs, anchor_t * (xs / anchor_n) ** STRASSEN_EXP,
            color="gray", ls=":", lw=1.2,
            label=r"referencia $\Theta(n^{\log_2 7})=\Theta(n^{2,807})$")

    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xlabel("n (dimensión)"); ax.set_ylabel("tiempo [ms]")
    ax.set_title("Matriz densa, dominio $D_{10}$\n"
                 "Comparación con las cotas asintóticas", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, "matrix_time_dense.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_normalized(rows, out_dir):
    """t/n^3 para el clásico y t/n^2,807 para Strassen: si el exponente teórico
    es el correcto, cada curva se aplana en su propia constante."""
    sub = [r for r in rows if r["domain"] == "D10"]
    agg = aggregate(sub, ["algorithm", "n", "type"])
    ns_all = sizes_of(sub)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    for ax, (algo, expo, texto) in zip(
            axes,
            [("naive", 3.0, r"$t/n^{3}$"),
             ("strassen", STRASSEN_EXP, r"$t/n^{2,807}$")]):
        for typ in TYPES:
            xs = [n for n in ns_all if (algo, n, typ) in agg]
            ys = [agg[(algo, n, typ)][0] * 1e6 / (n ** expo) for n in xs]
            if not xs:
                continue
            ax.plot(xs, ys, marker="o", markersize=4, lw=1.4, label=f"{typ}")
        ax.set_xscale("log", base=2); ax.set_yscale("log")
        ax.set_xlabel("n (dimensión)")
        ax.set_ylabel(texto + "  [ns por unidad]")
        ax.set_title(ALGO_LABEL[algo], fontsize=10)
        ax.legend(fontsize=8)
    fig.suptitle("Tiempo normalizado por la cota teórica de cada algoritmo "
                 "(dominio $D_{10}$): una curva plana confirma el exponente",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    path = os.path.join(out_dir, "matrix_normalized.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_speedup(rows, out_dir):
    """Cociente clásico/Strassen por tipo de matriz. Se restringe al dominio
    D10 para no mezclar dominios en una misma mediana."""
    rows = [r for r in rows if r["domain"] == "D10"]
    agg = aggregate(rows, ["algorithm", "n", "type"])
    ns_all = sizes_of(rows)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for typ in TYPES:
        xs, ys = [], []
        for n in ns_all:
            a, b = ("naive", n, typ), ("strassen", n, typ)
            if a in agg and b in agg and agg[b][0] > 0:
                xs.append(n); ys.append(agg[a][0] / agg[b][0])
        if not xs:
            continue
        ax.plot(xs, ys, marker="o", markersize=5, lw=1.6, label=f"matriz {typ}")
    ax.axhline(1.0, color="k", ls="--", lw=1.1,
               label="paridad (por debajo: Strassen es más lento)")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("n (dimensión)")
    ax.set_ylabel("tiempo clásico / tiempo Strassen")
    ax.set_title("Aceleración de Strassen frente al método clásico (dominio $D_{10}$)",
                 fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, "matrix_speedup.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_memory(rows, out_dir):
    agg = aggregate(rows, ["algorithm", "n"], field="heap")
    ns_all = sizes_of(rows)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for algo in ALGOS:
        xs = [n for n in ns_all if (algo, n) in agg]
        ys = [max(agg[(algo, n)][0], 1.0) for n in xs]
        if not xs:
            continue
        ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=6,
                color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.8)
    xs = np.array(ns_all, dtype=float)
    ax.plot(xs, 8 * xs ** 2, "k--", lw=1.1,
            label=r"referencia $8n^{2}$ bytes (matriz resultado)")

    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xlabel("n (dimensión)")
    ax.set_ylabel("pico de memoria auxiliar [bytes]")
    ax.set_title("Memoria dinámica auxiliar", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, "matrix_memory_vs_n.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_type_effect(rows, out_dir):
    """¿Aprovechan los algoritmos la estructura de la matriz? La respuesta
    esperada es que no: ninguno de los dos inspecciona los coeficientes."""
    n_max = max(sizes_of(rows))
    sub = [r for r in rows if r["n"] == n_max]
    agg = aggregate(sub, ["algorithm", "type", "domain"])

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    idx = np.arange(len(TYPES))
    width = 0.2
    k = 0
    for algo in ALGOS:
        for dom in DOMAINS:
            vals = [agg[(algo, t, dom)][0] if (algo, t, dom) in agg else 0.0
                    for t in TYPES]
            ax.bar(idx + (k - 1.5) * width, vals, width,
                   color=ALGO_COLOR[algo],
                   alpha=1.0 if dom == "D10" else 0.55,
                   label=f"{ALGO_LABEL[algo]}, {dom}")
            k += 1
    ax.set_xticks(idx); ax.set_xticklabels([f"matriz {t}" for t in TYPES])
    ax.set_ylabel("tiempo [ms]")
    ax.set_title(f"Efecto de la estructura y del dominio de la matriz "
                 f"(n = {n_max})", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, "matrix_type_effect.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_cutoff(sweep_rows, out_dir):
    """Barrido del umbral de corte de Strassen (archivo opcional)."""
    if not sweep_rows:
        return None
    sub = [r for r in sweep_rows if r["algorithm"] == "strassen"]
    if not sub:
        return None
    agg = aggregate(sub, ["n", "cutoff"])
    ns_all = sorted({k[0] for k in agg})
    cutoffs = sorted({k[1] for k in agg})

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for n in ns_all:
        xs = [c for c in cutoffs if (n, c) in agg]
        ys = [agg[(n, c)][0] for c in xs]
        if not xs:
            continue
        ax.plot(xs, ys, marker="o", markersize=5, lw=1.6, label=f"n = {n}")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xlabel("umbral de corte (dimensión a la que se delega en el clásico)")
    ax.set_ylabel("tiempo [ms]")
    ax.set_title("Strassen: efecto del umbral de corte\n"
                 "(umbral 1 = recursión pura hasta bloques 1x1)", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, "matrix_cutoff_sweep.png")
    fig.savefig(path); plt.close(fig)
    return path


def is_pow2(n):
    return n > 0 and (n & (n - 1)) == 0


def fig_stride(stride_rows, out_dir):
    """Control: costo por operación t/n^3 del método clásico en n = 2^k y en
    tamaños vecinos que ocupan la misma memoria pero cuyo stride de columna
    no es potencia de dos (archivo opcional, `make stride-check`)."""
    sub = [r for r in stride_rows if r["algorithm"] == "naive"]
    if not sub:
        return None
    agg = aggregate(sub, ["n"])
    ns_all = sorted(k[0] for k in agg)
    ys = [agg[(n,)][0] * 1e6 / n ** 3 for n in ns_all]

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    pw = [i for i, n in enumerate(ns_all) if is_pow2(n)]
    npw = [i for i, n in enumerate(ns_all) if not is_pow2(n)]
    ax.plot([ns_all[i] for i in npw], [ys[i] for i in npw], "o", markersize=6,
            color="#2ca02c", label="n no potencia de dos (stride $8n$ no alineado)")
    ax.plot([ns_all[i] for i in pw], [ys[i] for i in pw], "s", markersize=7,
            color="#d62728", label="n potencia de dos (stride $8n$ alineado a página)")
    for n, y in zip(ns_all, ys):
        ax.annotate(f"{n}", (n, y), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=7)
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xlabel("n (dimensión)")
    ax.set_ylabel(r"$t/n^{3}$  [ns por multiplicación escalar]")
    ax.set_title("Método clásico: costo por operación en $n=2^k$ y en tamaños vecinos\n"
                 "(matrices densas $D_{10}$; misma memoria, distinto alineamiento)",
                 fontsize=10)
    ax.set_ylim(top=ax.get_ylim()[1] * 1.6)          # aire para las etiquetas
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    path = os.path.join(out_dir, "matrix_stride_check.png")
    fig.savefig(path); plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Tablas LaTeX
# ---------------------------------------------------------------------------
# Cabecera de identificación que se antepone a cada archivo .tex generado, para
# cumplir el punto (4) de las condiciones de entrega (número de tarea, ramo,
# semestre, nombre y rol en todo lo entregado). En TeX el comentario va desde %
# hasta el final de la línea.
TEX_IDENT = (
    "% =============================================================================\n"
    "% INF-221 Algoritmos y Complejidad -- Tarea 1 -- Semestre 2026-2\n"
    "% Autor: Kurt Wiederhold   Rol: 202473528-4\n"
    "%\n"
    "% ARCHIVO GENERADO AUTOMATICAMENTE por\n"
    "% code/matrix_multiplication/scripts/plot_generator.py a partir de\n"
    "% data/measurements/matrix_multiplication_measurements.csv. No editar a mano:\n"
    "% se regenera con `make plots`.\n"
    "% =============================================================================\n"
)


def latex_header(caption, label, cols):
    r"""Cabecera de tabla LaTeX.

    Se usan \hline y no booktabs porque report/preamble.tex —que el enunciado
    prohíbe modificar— no carga el paquete booktabs.
    """
    return (TEX_IDENT +
            "\\begin{table}[H]\n\\centering\n\\small\n"
            f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
            f"\\begin{{tabular}}{{{cols}}}\n\\hline\\hline\n")


LATEX_FOOTER = "\\hline\\hline\n\\end{tabular}\n\\end{table}\n"
MIDRULE = "\\hline\n"


def fmt_ms(v):
    """Tiempo en milisegundos con coma decimal (convención en español)."""
    if v is None:
        return "--"
    if v >= 100:
        s = f"{v:.0f}"
    elif v >= 1:
        s = f"{v:.2f}"
    elif v >= 1e-2:
        s = f"{v:.4f}"
    else:
        mantisa, exp = f"{v:.2e}".split("e")
        return ("$" + mantisa.replace(".", "{,}") +
                "\\times 10^{" + str(int(exp)) + "}$")
    return s.replace(".", "{,}")


def table_time(rows, out_dir):
    sub = [r for r in rows if r["type"] == "densa" and r["domain"] == "D10"]
    agg = aggregate(sub, ["algorithm", "n"])
    ns_all = sizes_of(sub)

    lines = [latex_header(
        "Tiempo mediano [ms], matrices \\emph{densas} con dominio $D_{10}$, "
        f"umbral de corte de Strassen {rows[0]['cutoff']}; última fila: cociente.",
        "tab:matrix-time",
        "l" + "r" * len(ns_all))]
    lines.append("Algoritmo & " +
                 " & ".join(f"$n=2^{{{int(round(math.log2(n)))}}}$" for n in ns_all) +
                 " \\\\\n")
    lines.append(MIDRULE)
    for algo in ALGOS:
        vals = [agg[(algo, n)][0] if (algo, n) in agg else None for n in ns_all]
        lines.append(f"{ALGO_LABEL[algo]} & " +
                     " & ".join(fmt_ms(v) for v in vals) + " \\\\\n")
    lines.append(MIDRULE + "Clásico / Strassen & " + " & ".join(
        (f"{agg[('naive', n)][0] / agg[('strassen', n)][0]:.2f}".replace(".", "{,}")
         if ('naive', n) in agg and ('strassen', n) in agg
         and agg[('strassen', n)][0] > 0 else "--")
        for n in ns_all) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_matrix_time.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def table_memory(rows, out_dir):
    agg = aggregate(rows, ["algorithm", "n"], field="heap")
    ns_all = sizes_of(rows)

    lines = [latex_header(
        "Pico de memoria dinámica auxiliar. Para el método clásico corresponde "
        "esencialmente a la matriz resultado ($8n^{2}$ bytes); Strassen añade "
        "los bloques temporales de la recursión.",
        "tab:matrix-memory",
        "l" + "r" * len(ns_all))]
    lines.append("Algoritmo & " +
                 " & ".join(f"$n=2^{{{int(round(math.log2(n)))}}}$" for n in ns_all) +
                 " \\\\\n")
    lines.append(MIDRULE)
    for algo in ALGOS:
        cells = []
        for n in ns_all:
            k = (algo, n)
            cells.append(human_bytes(agg[k][0]).replace(" ", "~") if k in agg else "--")
        lines.append(f"{ALGO_LABEL[algo]} & " + " & ".join(cells) + " \\\\\n")
    lines.append(MIDRULE + "Sobrecosto de Strassen & " + " & ".join(
        (f"{agg[('strassen', n)][0] / agg[('naive', n)][0]:.2f}$\\times$".replace(".", "{,}")
         if ('naive', n) in agg and ('strassen', n) in agg and agg[('naive', n)][0] > 0
         else "--")
        for n in ns_all) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_matrix_memory.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def strassen_active(rows):
    """Filas de Strassen en las que la recursión realmente se ejecuta, es decir
    con n mayor que el umbral de corte. Para n <= umbral, Strassen delega por
    completo en el método clásico y medir su 'exponente' ahí sería medir el
    del clásico."""
    return [r for r in rows if r["algorithm"] == "strassen" and r["n"] > r["cutoff"]]


def exponent_cells(rows, algo, typ):
    """Devuelve (p, r2, n_puntos) del ajuste para un algoritmo y tipo."""
    sub = [r for r in rows if r["algorithm"] == algo
           and r["type"] == typ and r["domain"] == "D10"]
    if algo == "strassen":
        sub = [r for r in sub if r["n"] > r["cutoff"]]
    if not sub:
        return None
    agg = aggregate(sub, ["n"])
    ns_all = sorted(k[0] for k in agg)
    p, _c, r2 = fit_exponent(ns_all, [agg[(n,)][0] for n in ns_all])
    return p, r2, len(ns_all)


def table_exponents(rows, out_dir):
    lines = [latex_header(
        "Exponente empírico $p$ del ajuste $t = c\\,n^{p}$ por mínimos cuadrados "
        "sobre los logaritmos (dominio $D_{10}$). Los valores de referencia son "
        "$3$ para el método clásico y $\\log_2 7 = 2{,}807$ para Strassen. "
        "Entre paréntesis, el coeficiente de determinación $R^2$. Para Strassen "
        "se usan sólo los tamaños en que la recursión está activa ($n$ mayor "
        "que el umbral de corte); con umbral 64 son dos puntos, así que $p$ es "
        "la pendiente entre ellos y no hay $R^2$.",
        "tab:matrix-exponents",
        "l" + "r" * len(TYPES))]
    lines.append("Algoritmo & " + " & ".join(f"matriz {t}" for t in TYPES) +
                 " \\\\\n")
    lines.append(MIDRULE)
    for algo in ALGOS:
        cells = []
        for typ in TYPES:
            res = exponent_cells(rows, algo, typ)
            if res is None:
                cells.append("--"); continue
            p, r2, npts = res
            if npts >= 3:
                cells.append(f"{p:.3f} ({r2:.3f})".replace(".", "{,}"))
            else:
                cells.append(f"{p:.3f} ({npts} puntos)".replace(".", "{,}"))
        lines.append(f"{ALGO_LABEL[algo]} & " + " & ".join(cells) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_matrix_exponents.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def table_stride(stride_rows, out_dir):
    """Costo por operación del método clásico en n = 2^k y en sus vecinos."""
    sub = [r for r in stride_rows if r["algorithm"] == "naive"]
    if not sub:
        return None
    agg = aggregate(sub, ["n"])
    ns_all = sorted(k[0] for k in agg)

    lines = [latex_header(
        "Control (\\texttt{make stride-check}): tiempo y costo por operación del "
        "clásico, matrices densas $D_{10}$, en $n=2^{k}$ y en dimensiones vecinas "
        "de igual memoria; sólo cambia el alineamiento del salto de $8n$ bytes.",
        "tab:matrix-stride",
        "l" + "r" * len(ns_all))]
    lines.append("$n$ & " + " & ".join(
        (f"$\\mathbf{{{n}}}$" if is_pow2(n) else f"{n}") for n in ns_all) + " \\\\\n")
    lines.append(MIDRULE)
    lines.append("tiempo [ms] & " + " & ".join(fmt_ms(agg[(n,)][0]) for n in ns_all) + " \\\\\n")
    lines.append("$t/n^{3}$ [ns] & " + " & ".join(
        f"{agg[(n,)][0] * 1e6 / n ** 3:.2f}".replace(".", "{,}") for n in ns_all) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_matrix_stride.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


# ---------------------------------------------------------------------------
# Macros numéricas para la prosa del informe
# ---------------------------------------------------------------------------
def numbers_tex(rows, sweep, stride, typecheck, out_dir):
    r"""Escribe numbers_matrix.tex: un \newcommand por cada valor que la prosa
    del informe cita, calculado desde los CSV. Si un experimento opcional no se
    ha ejecutado, sus macros se definen como '--' para que el informe compile."""
    agg = aggregate(rows, ["algorithm", "n", "type", "domain"])
    ns_all = sizes_of(rows)
    n_max = max(ns_all)
    n_mid = ns_all[-2] if len(ns_all) > 1 else n_max

    def med(algo, n, typ="densa", dom="D10"):
        return agg[(algo, n, typ, dom)][0]

    m = {}
    m["MatNumRows"] = tex_num(len(rows), 0)
    m["MatNumIncorrect"] = tex_num(sum(1 for r in rows if r["correct"] == 0), 0)
    m["MatSweepRows"] = tex_num(len(sweep), 0)
    m["MatStrideRows"] = tex_num(len(stride), 0)
    m["MatTypeCheckRows"] = tex_num(len(typecheck), 0)
    m["MatCutoff"] = tex_num(rows[0]["cutoff"], 0)
    m["MatNMaxLog"] = tex_num(round(math.log2(n_max)), 0)
    m["MatNMidLog"] = tex_num(round(math.log2(n_mid)), 0)

    # Tiempos y aceleración (densa D10).
    m["MatNaiveMaxMs"] = tex_num(med("naive", n_max), 0)
    m["MatStrassenMaxMs"] = tex_num(med("strassen", n_max), 0)
    m["MatSpeedupMax"] = tex_num(med("naive", n_max) / med("strassen", n_max))
    m["MatSpeedupMid"] = tex_num(med("naive", n_mid) / med("strassen", n_mid))
    m["MatNaiveMidMs"] = tex_num(med("naive", n_mid))

    # Memoria (máximo n).
    heap = aggregate(rows, ["algorithm", "n"], field="heap")
    m["MatNaiveMemMax"] = human_bytes(heap[("naive", n_max)][0]).replace(" ", "~")
    m["MatStrassenMemMax"] = human_bytes(heap[("strassen", n_max)][0]).replace(" ", "~")
    m["MatMemRatio"] = tex_num(heap[("strassen", n_max)][0] / heap[("naive", n_max)][0], 1)

    # Exponentes (densa D10) y R^2 mínimo del clásico.
    p_n, r2_n, _ = exponent_cells(rows, "naive", "densa")
    p_s, _r2_s, npts_s = exponent_cells(rows, "strassen", "densa")
    m["MatExpNaive"] = tex_num(p_n, 3)
    m["MatExpStrassen"] = tex_num(p_s, 3)
    m["MatExpStrassenPts"] = tex_num(npts_s, 0)
    r2s = [exponent_cells(rows, "naive", t)[1] for t in TYPES]
    m["MatRsqNaiveMin"] = tex_num(min(r2s), 3)

    # Barrido de umbral (densa D10, n = n_mid, el mayor del barrido).
    sw = [r for r in sweep if r["algorithm"] == "strassen" and r["type"] == "densa"
          and r["domain"] == "D10"]
    if sw:
        n_sw = max(r["n"] for r in sw)
        a = aggregate([r for r in sw if r["n"] == n_sw], ["cutoff"])
        cuts = sorted(k[0] for k in a)
        best = min(cuts, key=lambda c: a[(c,)][0])
        default = rows[0]["cutoff"]
        naive_ref = med("naive", n_sw)
        m["MatSweepN"] = tex_num(n_sw, 0)
        m["MatSweepNLog"] = tex_num(round(math.log2(n_sw)), 0)
        m["MatSweepPureMs"] = tex_num(a[(cuts[0],)][0], 1)
        m["MatSweepPureOverNaive"] = tex_num(a[(cuts[0],)][0] / naive_ref, 1)
        m["MatSweepBestCut"] = tex_num(best, 0)
        m["MatSweepBestMs"] = tex_num(a[(best,)][0])
        m["MatSweepBestOverPure"] = tex_num(a[(cuts[0],)][0] / a[(best,)][0], 1)
        m["MatSweepNaiveOverBest"] = tex_num(naive_ref / a[(best,)][0])
        m["MatSweepDefaultMs"] = tex_num(a[(default,)][0]) if (default,) in a else "--"
    else:
        for k in ("MatSweepN", "MatSweepNLog", "MatSweepPureMs", "MatSweepPureOverNaive",
                  "MatSweepBestCut", "MatSweepBestMs", "MatSweepBestOverPure",
                  "MatSweepNaiveOverBest", "MatSweepDefaultMs"):
            m[k] = "--"

    # Tipo de matriz: dispersión en la corrida principal y en el control.
    main_vals = [med("naive", n_max, t, d) for t in TYPES for d in DOMAINS]
    m["MatTypeDispMain"] = tex_num((max(main_vals) / min(main_vals) - 1) * 100, 0)
    tc = [r for r in typecheck if r["algorithm"] == "naive"]
    if tc:
        a = aggregate(tc, ["type"])
        vals = {t: a[(t,)][0] for t in TYPES if (t,) in a}
        m["MatTypeDispCtrl"] = tex_num((max(vals.values()) / min(vals.values()) - 1) * 100, 0)
        for t in TYPES:
            m["MatCtrl" + t.capitalize() + "Ms"] = tex_num(vals[t], 0) if t in vals else "--"
        # Desplazamiento del nivel absoluto: mediana del control / mediana de la
        # corrida principal para los mismos casos (n_max, D10, muestra a).
        same = [r for r in rows if r["algorithm"] == "naive" and r["n"] == n_max
                and r["domain"] == "D10" and r["sample"] == "a"]
        ref = float(np.median([r["time_ms"] for r in same]))
        ctrl = float(np.median([r["time_ms"] for r in tc]))
        m["MatCtrlShiftPct"] = tex_num((ctrl / ref - 1) * 100, 0)
    else:
        for k in ("MatTypeDispCtrl", "MatCtrlDensaMs", "MatCtrlDiagonalMs",
                  "MatCtrlDispersaMs", "MatCtrlShiftPct"):
            m[k] = "--"

    # Control de stride: potencia de dos frente a vecinos.
    st = [r for r in stride if r["algorithm"] == "naive"]
    if st:
        a = aggregate(st, ["n"])
        ns = sorted(k[0] for k in a)
        nsop = {n: a[(n,)][0] * 1e6 / n ** 3 for n in ns}
        pows = [n for n in ns if is_pow2(n)]
        big = max(pows)
        neigh = [n for n in ns if not is_pow2(n) and abs(n - big) < big / 4]
        m["MatStrideN"] = tex_num(big, 0)
        m["MatStrideNsPow"] = tex_num(nsop[big])
        m["MatStrideNsNeighMin"] = tex_num(min(nsop[n] for n in neigh))
        m["MatStrideNsNeighMax"] = tex_num(max(nsop[n] for n in neigh))
        m["MatStrideNeighLo"] = tex_num(min(neigh), 0)
        m["MatStrideNeighHi"] = tex_num(max(neigh), 0)
        m["MatStrideFactor"] = tex_num(nsop[big] / np.mean([nsop[n] for n in neigh]), 1)
        # Rango de t/n^3 sobre todos los tamaños NO potencia de dos.
        non = [nsop[n] for n in ns if not is_pow2(n)]
        m["MatStrideNonPowMin"], m["MatStrideNonPowMax"] = tex_num(min(non)), tex_num(max(non))
        m["MatStrideNonPowRatio"] = tex_num(max(non) / min(non), 1)
        pw_vals = [nsop[n] for n in pows]
        m["MatStridePowRatio"] = tex_num(max(pw_vals) / min(pw_vals), 1)
        # Qué tardaría el clásico en n_max al costo por operación de sus
        # vecinos, y cuánto le sacaría Strassen entonces.
        equiv = np.mean([nsop[n] for n in neigh]) * n_max ** 3 / 1e6
        m["MatStrideEquivMs"] = tex_num(equiv, 0)
        m["MatStrideEquivSpeedup"] = tex_num(equiv / med("strassen", n_max))
    else:
        for k in ("MatStrideN", "MatStrideNsPow", "MatStrideNsNeighMin", "MatStrideNsNeighMax",
                  "MatStrideNeighLo", "MatStrideNeighHi", "MatStrideFactor",
                  "MatStrideNonPowMin", "MatStrideNonPowMax", "MatStrideNonPowRatio",
                  "MatStridePowRatio", "MatStrideEquivMs", "MatStrideEquivSpeedup"):
            m[k] = "--"

    lines = [TEX_IDENT.replace("ARCHIVO GENERADO", "MACROS NUMERICAS. ARCHIVO GENERADO")]
    for k in sorted(m):
        lines.append(f"\\newcommand{{\\{k}}}{{{m[k]}}}\n")
    path = os.path.join(out_dir, "numbers_matrix.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(
        description="Genera los graficos y tablas del experimento de matrices.")
    p.add_argument("--csv", default=DEFAULT_CSV, help="CSV de mediciones")
    p.add_argument("--sweep-csv", default=SWEEP_CSV,
                   help="CSV del barrido de umbral (opcional)")
    p.add_argument("--stride-csv", default=STRIDE_CSV,
                   help="CSV del control de stride (opcional)")
    p.add_argument("--typecheck-csv", default=TYPECHECK_CSV,
                   help="CSV del control tipo/orden (opcional)")
    p.add_argument("--out", default=DEFAULT_PLOTS, help="directorio de graficos")
    p.add_argument("--tables", default=DEFAULT_TABLES,
                   help="directorio de las tablas LaTeX")
    args = p.parse_args(argv)

    rows = load(args.csv)
    sweep = load(args.sweep_csv, required=False)
    stride = load(args.stride_csv, required=False)
    typecheck = load(args.typecheck_csv, required=False)
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(args.tables, exist_ok=True)

    incorrectas = sum(1 for r in rows if r["correct"] == 0)
    if incorrectas:
        print(f"AVISO: {incorrectas} mediciones marcadas como incorrectas en el CSV.")

    print(f"Leidas {len(rows)} mediciones de {args.csv}")
    if sweep:
        print(f"Leidas {len(sweep)} mediciones del barrido de umbral.")
    if stride:
        print(f"Leidas {len(stride)} mediciones del control de stride.")
    if typecheck:
        print(f"Leidas {len(typecheck)} mediciones del control tipo/orden.")

    generated = []
    for fn in (fig_time_vs_n, fig_time_dense, fig_normalized, fig_speedup,
               fig_memory, fig_type_effect):
        path = fn(rows, args.out)
        if path:
            generated.append(path)
    for path in (fig_cutoff(sweep, args.out), fig_stride(stride, args.out)):
        if path:
            generated.append(path)
    for fn in (table_time, table_memory, table_exponents):
        generated.append(fn(rows, args.tables))
    path = table_stride(stride, args.tables)
    if path:
        generated.append(path)
    generated.append(numbers_tex(rows, sweep, stride, typecheck, args.tables))

    print("\nArchivos generados:")
    for g in generated:
        print("  " + os.path.relpath(g, PROJECT_DIR).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
