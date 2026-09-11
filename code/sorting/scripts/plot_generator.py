#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 INF-221 Algoritmos y Complejidad -- Semestre 2026-2
 Tarea 1: «Más allá de la notación asintótica»
 Autor: Kurt Wiederhold        Rol: 202473528-4

 Archivo: code/sorting/scripts/plot_generator.py

 Lee data/measurements/sorting_measurements.csv (producido por ./sorting) y
 genera en data/plots/ los gráficos del mini-informe, además de las tablas
 LaTeX en data/measurements/ que el informe incluye con \\input.

 TODA figura y TODA tabla del informe salen de este script: no hay ningún
 número escrito a mano. Basta volver a ejecutar `make experiment` para
 regenerarlo todo desde cero.

 Estadístico usado: la MEDIANA sobre las repeticiones y las tres muestras
 aleatorias {a,b,c}. Se prefiere a la media porque el ruido del sistema
 operativo (planificación, interrupciones, migración entre núcleos) produce
 valores atípicos altos pero nunca bajos; la mediana es robusta frente a esa
 asimetría. La dispersión se reporta como rango intercuartílico.

 Figuras generadas:
   sorting_time_vs_n.png           tiempo vs n, panel por tipo y dominio
   sorting_time_random_D7.png      caso de referencia con cotas teóricas
   sorting_normalized_nlogn.png    t/(n log n): revela las constantes ocultas
   sorting_memory_vs_n.png         memoria auxiliar vs n
   sorting_input_type_effect.png   efecto del orden inicial de la entrada
   sorting_speedup_vs_stdsort.png  costo relativo frente a std::sort

 Tablas generadas (LaTeX):
   table_sorting_time.tex          tiempos medianos por algoritmo y n
   table_sorting_memory.tex        memoria auxiliar por algoritmo y n
   table_sorting_exponents.tex     exponente empírico ajustado por regresión

 Macros generadas (LaTeX):
   numbers_sorting.tex             cada número que el informe cita en su prosa
                                   (razones, factores, tiempos puntuales) como
                                   un \newcommand calculado desde el CSV, de
                                   modo que el texto no contiene valores
                                   escritos a mano y no queda desincronizado si
                                   se repite el experimento.

 Uso:  python scripts/plot_generator.py [--csv RUTA] [--out DIR]

 Referencias:
  [1] Documentación de Matplotlib, https://matplotlib.org/stable/
  [2] McGeoch, C. C. «A Guide to Experimental Algorithmics», CUP, 2012
      (uso de la mediana y de gráficos log-log; estimación del exponente
       empírico por regresión sobre los logaritmos).
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
matplotlib.use("Agg")          # backend sin ventana: imprescindible en `make`
import matplotlib.pyplot as plt

# --- Rutas resueltas respecto de la ubicación de ESTE archivo ----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)                  # code/sorting
DEFAULT_CSV = os.path.join(PROJECT_DIR, "data", "measurements",
                           "sorting_measurements.csv")
DEFAULT_PLOTS = os.path.join(PROJECT_DIR, "data", "plots")
DEFAULT_TABLES = os.path.join(PROJECT_DIR, "data", "measurements")

# --- Presentación uniforme ---------------------------------------------------
ALGOS = ["std_sort", "merge_sort", "quick_sort", "patience_sort"]
ALGO_LABEL = {
    "std_sort": "std::sort",
    "merge_sort": "Merge sort",
    "quick_sort": "Quick sort",
    "patience_sort": "Patience sort",
}
ALGO_COLOR = {
    "std_sort": "#1f77b4",
    "merge_sort": "#d62728",
    "quick_sort": "#2ca02c",
    "patience_sort": "#9467bd",
}
ALGO_MARKER = {
    "std_sort": "o",
    "merge_sort": "s",
    "quick_sort": "^",
    "patience_sort": "D",
}
TYPES = ["aleatorio", "ascendente", "descendente"]
DOMAINS = ["D1", "D7"]
DOMAIN_LABEL = {"D1": r"$D_1=\{0,\dots,9\}$", "D7": r"$D_7=\{0,\dots,10^7\}$"}

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
# Lectura y agregación
# ---------------------------------------------------------------------------
def load(csv_path):
    """Devuelve las filas del CSV con los campos numéricos ya convertidos."""
    if not os.path.isfile(csv_path):
        sys.exit(f"Error: no existe {csv_path}\n"
                 f"Ejecute primero el programa de mediciones (make run).")
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
                    "correct": int(r["correct"]),
                })
            except (KeyError, ValueError):
                continue
    if not rows:
        sys.exit(f"Error: {csv_path} no contiene mediciones legibles.")
    return rows


def aggregate(rows, keys, field="time_ms"):
    """Agrupa por `keys` y devuelve {clave: (mediana, q1, q3, n_obs)}."""
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
    """Ajusta t = c * n^p por mínimos cuadrados sobre los logaritmos.

    Devuelve (p, c, r2). Es la forma estándar de estimar el exponente empírico:
    en escala log-log la ley de potencias es una recta cuya pendiente es p.
    """
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
    fino como separador de miles (\\,). tex_num(2468.6, 0) -> '2\\,469'."""
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
    """Panorama completo: una fila por dominio, una columna por tipo de orden."""
    agg = aggregate(rows, ["algorithm", "n", "type", "domain"])
    ns_all = sizes_of(rows)

    fig, axes = plt.subplots(len(DOMAINS), len(TYPES),
                             figsize=(11, 6.4), sharex=True, sharey=True)
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
                ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=4,
                        color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.4)
                ax.fill_between(xs, lo, hi, color=ALGO_COLOR[algo], alpha=0.18,
                                linewidth=0)
            ax.set_xscale("log"); ax.set_yscale("log")
            if i == 0:
                ax.set_title(f"Entrada {typ}", fontsize=10)
            if j == 0:
                ax.set_ylabel(f"{DOMAIN_LABEL[dom]}\ntiempo [ms]")
            if i == len(DOMAINS) - 1:
                ax.set_xlabel("n (elementos)")

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("Tiempo de ordenamiento en función de n\n"
                 "(mediana de 3 muestras x repeticiones; banda = rango intercuartílico)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0.05, 1, 0.94])
    path = os.path.join(out_dir, "sorting_time_vs_n.png")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


def fig_time_random(rows, out_dir):
    """Caso de referencia (aleatorio, D7) con las cotas teóricas superpuestas."""
    sub = [r for r in rows if r["type"] == "aleatorio" and r["domain"] == "D7"]
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
        ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=5,
                color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.6)

    # Cotas teóricas ancladas al punto de std::sort con el mayor n, de modo que
    # la comparación sea de FORMA (pendiente) y no de magnitud absoluta.
    anchor_n = max(n for n in ns_all if ("std_sort", n) in agg)
    anchor_t = agg[("std_sort", anchor_n)][0]
    xs = np.array(ns_all, dtype=float)
    ax.plot(xs, anchor_t * (xs * np.log2(xs)) / (anchor_n * math.log2(anchor_n)),
            "k--", lw=1.1, label=r"referencia $\Theta(n\log n)$")
    ax.plot(xs, anchor_t * xs / anchor_n,
            color="gray", ls=":", lw=1.1, label=r"referencia $\Theta(n)$")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("n (elementos)"); ax.set_ylabel("tiempo [ms]")
    ax.set_title("Entrada aleatoria, dominio $D_7$\n"
                 "Comparación con las cotas asintóticas", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(out_dir, "sorting_time_random_D7.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_normalized(rows, out_dir):
    """t/(n log2 n): si la complejidad es Θ(n log n), la curva se aplana y su
    altura es exactamente el factor constante que la notación asintótica oculta."""
    fig, axes = plt.subplots(1, len(TYPES), figsize=(11, 3.7), sharey=True)
    for j, typ in enumerate(TYPES):
        ax = axes[j]
        sub = [r for r in rows if r["type"] == typ and r["domain"] == "D7"]
        agg = aggregate(sub, ["algorithm", "n"])
        ns_all = sizes_of(sub)
        for algo in ALGOS:
            xs = [n for n in ns_all if (algo, n) in agg and n > 1]
            ys = [agg[(algo, n)][0] * 1e6 / (n * math.log2(n)) for n in xs]
            if not xs:
                continue
            ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=4,
                    color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.4)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("n (elementos)")
        ax.set_title(f"Entrada {typ}", fontsize=10)
        if j == 0:
            ax.set_ylabel(r"$t/(n\log_2 n)$  [ns por operación]")
    axes[0].legend(fontsize=8)
    fig.suptitle("Tiempo normalizado por $n\\log_2 n$ (dominio $D_7$): "
                 "una curva plana confirma el orden $\\Theta(n\\log n)$ y su "
                 "altura es la constante oculta", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    path = os.path.join(out_dir, "sorting_normalized_nlogn.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_memory(rows, out_dir):
    """Memoria auxiliar (máximo) frente a n, con la referencia lineal 4n bytes.

    Se dibuja además el caso ascendente-$D_7$ de patience sort por separado,
    porque es el único en que el consumo depende del orden de la entrada: con
    todos los elementos distintos y ya ordenados se abre una pila por elemento.
    """
    peaks = defaultdict(int)
    for r in rows:
        peaks[(r["algorithm"], r["n"])] = max(peaks[(r["algorithm"], r["n"])],
                                              r["heap"])
    typical = defaultdict(int)
    for r in rows:
        if r["type"] == "aleatorio":
            k = (r["algorithm"], r["n"])
            typical[k] = max(typical[k], r["heap"])
    ns_all = sizes_of(rows)

    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    for algo in ALGOS:
        xs = [n for n in ns_all if (algo, n) in typical]
        ys = [max(typical[(algo, n)], 0.5) for n in xs]   # 0 -> 0,5 para el log
        if not xs:
            continue
        ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=5,
                color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.6)

    xs_p = [n for n in ns_all if ("patience_sort", n) in peaks]
    ys_p = [max(peaks[("patience_sort", n)], 0.5) for n in xs_p]
    ax.plot(xs_p, ys_p, marker=ALGO_MARKER["patience_sort"], markersize=5,
            color=ALGO_COLOR["patience_sort"], lw=1.4, ls="--",
            label="Patience sort (peor caso: ascendente $D_7$)")

    xs = np.array(ns_all, dtype=float)
    ax.plot(xs, 4 * xs, "k--", lw=1.1,
            label=r"copia de retorno $4n$ bytes (firma provista); por encima: memoria auxiliar")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("n (elementos)")
    ax.set_ylabel("pico de memoria dinámica de la llamada [bytes]")
    ax.set_title("Memoria dinámica de la llamada completa\n"
                 "(incluye la copia de retorno de $4n$ bytes común a los cuatro "
                 "algoritmos)", fontsize=10)
    ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    path = os.path.join(out_dir, "sorting_memory_vs_n.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_input_type_effect(rows, out_dir):
    """Cuánto cambia el tiempo según el orden inicial, para el mayor n medido."""
    n_max = max(sizes_of(rows))
    sub = [r for r in rows if r["n"] == n_max]
    agg = aggregate(sub, ["algorithm", "type", "domain"])

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), sharey=False)
    width = 0.2
    idx = np.arange(len(TYPES))
    for a, dom in enumerate(DOMAINS):
        ax = axes[a]
        for k, algo in enumerate(ALGOS):
            vals = [agg[(algo, t, dom)][0] if (algo, t, dom) in agg else 0.0
                    for t in TYPES]
            ax.bar(idx + (k - 1.5) * width, vals, width,
                   color=ALGO_COLOR[algo], label=ALGO_LABEL[algo])
        ax.set_xticks(idx); ax.set_xticklabels(TYPES)
        ax.set_yscale("log")
        ax.set_ylabel("tiempo [ms]")
        ax.set_title(f"n = {n_max:,}".replace(",", " ") +
                     f",  dominio {dom}", fontsize=10)
    axes[0].legend(fontsize=8)
    fig.suptitle("Sensibilidad al orden inicial de la entrada", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(out_dir, "sorting_input_type_effect.png")
    fig.savefig(path); plt.close(fig)
    return path


def fig_speedup(rows, out_dir):
    """Tiempo relativo a std::sort: cuántas veces más lento es cada algoritmo.

    Se restringe al dominio D7 para no mezclar en una misma mediana dos
    dominios con costos muy distintos (véase fig_input_type_effect)."""
    rows = [r for r in rows if r["domain"] == "D7"]
    agg = aggregate(rows, ["algorithm", "n", "type"])
    ns_all = sizes_of(rows)

    fig, axes = plt.subplots(1, len(TYPES), figsize=(11, 3.6), sharey=True)
    for j, typ in enumerate(TYPES):
        ax = axes[j]
        for algo in ALGOS:
            if algo == "std_sort":
                continue
            xs, ys = [], []
            for n in ns_all:
                k, base = (algo, n, typ), ("std_sort", n, typ)
                if k in agg and base in agg and agg[base][0] > 0:
                    xs.append(n); ys.append(agg[k][0] / agg[base][0])
            if not xs:
                continue
            ax.plot(xs, ys, marker=ALGO_MARKER[algo], markersize=4,
                    color=ALGO_COLOR[algo], label=ALGO_LABEL[algo], lw=1.4)
        ax.axhline(1.0, color="#1f77b4", ls="--", lw=1.1, label="std::sort")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("n (elementos)")
        ax.set_title(f"Entrada {typ}", fontsize=10)
        if j == 0:
            ax.set_ylabel("tiempo relativo a std::sort")
    axes[0].legend(fontsize=8)
    fig.suptitle("Costo relativo frente a la implementación de la biblioteca "
                 "estándar, dominio $D_7$ (valores > 1: más lento)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    path = os.path.join(out_dir, "sorting_speedup_vs_stdsort.png")
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
    "% ARCHIVO GENERADO AUTOMATICAMENTE por code/sorting/scripts/plot_generator.py\n"
    "% a partir de data/measurements/sorting_measurements.csv. No editar a mano:\n"
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
    """Tiempos medianos (ms) por algoritmo y n, para la entrada aleatoria D7."""
    sub = [r for r in rows if r["type"] == "aleatorio" and r["domain"] == "D7"]
    agg = aggregate(sub, ["algorithm", "n"])
    ns_all = sizes_of(sub)

    lines = [latex_header(
        "Tiempo mediano [ms], entrada \\emph{aleatoria} con dominio $D_7$ "
        "(mediana sobre las tres muestras y todas las repeticiones).",
        "tab:sorting-time",
        "l" + "r" * len(ns_all))]
    lines.append("Algoritmo & " +
                 " & ".join(f"$n=10^{{{int(round(math.log10(n)))}}}$" for n in ns_all) +
                 " \\\\\n")
    lines.append(MIDRULE)
    for algo in ALGOS:
        vals = [agg[(algo, n)][0] if (algo, n) in agg else None for n in ns_all]
        lines.append(f"{ALGO_LABEL[algo]} & " +
                     " & ".join(fmt_ms(v) for v in vals) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_sorting_time.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def table_memory(rows, out_dir):
    """Pico de memoria auxiliar por algoritmo y n.

    Se reporta el MÁXIMO sobre tipos de entrada, dominios y muestras, no la
    mediana: el pico de memoria es por definición una cantidad de peor caso, y
    en patience sort depende fuertemente del orden inicial (la entrada
    ascendente con dominio $D_7$ genera una pila por elemento y duplica el
    consumo). Para los otros tres algoritmos el valor no varía.
    """
    peaks = defaultdict(int)
    for r in rows:
        k = (r["algorithm"], r["n"])
        peaks[k] = max(peaks[k], r["heap"])
    agg = {k: (v, v, v, 1) for k, v in peaks.items()}
    ns_all = sizes_of(rows)

    lines = [latex_header(
        "Pico de memoria dinámica de la llamada (máximo sobre órdenes, dominios "
        "y muestras), incluida la copia de retorno de $4n$ bytes de la firma "
        "provista: un valor de exactamente $4n$ significa sin memoria auxiliar propia.",
        "tab:sorting-memory",
        "l" + "r" * len(ns_all))]
    lines.append("Algoritmo & " +
                 " & ".join(f"$n=10^{{{int(round(math.log10(n)))}}}$" for n in ns_all) +
                 " \\\\\n")
    lines.append(MIDRULE)
    for algo in ALGOS:
        cells = []
        for n in ns_all:
            k = (algo, n)
            cells.append(human_bytes(agg[k][0]).replace(" ", "~") if k in agg else "--")
        lines.append(f"{ALGO_LABEL[algo]} & " + " & ".join(cells) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_sorting_memory.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def table_exponents(rows, out_dir):
    """Exponente empírico p del ajuste t = c n^p, por algoritmo y tipo."""
    ns_all = sizes_of(rows)
    # Pendiente que tendría un algoritmo exactamente n log2 n en este rango.
    p_nlogn, _, _ = fit_exponent(ns_all, [n * math.log2(n) for n in ns_all])
    lines = [latex_header(
        "Exponente empírico $p$ de $t = c\\,n^{p}$ (mínimos cuadrados en log-log, "
        f"dominio $D_7$). Un $\\Theta(n\\log n)$ debe dar $p\\approx{tex_num(p_nlogn)}$, "
        "la pendiente de $n\\log_2 n$ en el rango medido. Entre paréntesis, $R^2$.",
        "tab:sorting-exponents",
        "l" + "r" * len(TYPES))]
    lines.append("Algoritmo & " + " & ".join(TYPES) + " \\\\\n")
    lines.append(MIDRULE)

    for algo in ALGOS:
        cells = []
        for typ in TYPES:
            sub = [r for r in rows
                   if r["algorithm"] == algo and r["type"] == typ
                   and r["domain"] == "D7"]
            if not sub:
                cells.append("--"); continue
            agg = aggregate(sub, ["n"])
            ns_all = sorted(k[0] for k in agg)
            p, _c, r2 = fit_exponent(ns_all, [agg[(n,)][0] for n in ns_all])
            cells.append(f"{p:.3f} ({r2:.3f})".replace(".", "{,}"))
        lines.append(f"{ALGO_LABEL[algo]} & " + " & ".join(cells) + " \\\\\n")
    lines.append(LATEX_FOOTER)

    path = os.path.join(out_dir, "table_sorting_exponents.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


# ---------------------------------------------------------------------------
# Macros numéricas para la prosa del informe
# ---------------------------------------------------------------------------
def numbers_tex(rows, out_dir):
    r"""Escribe numbers_sorting.tex: un \newcommand por cada valor que la prosa
    del informe cita. Todo se calcula aquí desde el CSV; el informe sólo usa
    los nombres. Las definiciones son globales, así que basta un \input al
    comienzo del documento (sections/experiment_intro.tex)."""
    agg = aggregate(rows, ["algorithm", "n", "type", "domain"])
    ns_all = sizes_of(rows)
    n_max, n_small, n_mid = max(ns_all), 10 ** 3, 10 ** 5

    def med(algo, n, typ, dom):
        return agg[(algo, n, typ, dom)][0]

    m = {}
    m["SortNumRows"] = tex_num(len(rows), 0)
    m["SortNumIncorrect"] = tex_num(sum(1 for r in rows if r["correct"] == 0), 0)

    # Exponentes empíricos (dominio D7): mínimo y máximo sobre algoritmos/tipos.
    exps = []
    for algo in ALGOS:
        for typ in TYPES:
            sub = [r for r in rows if r["algorithm"] == algo
                   and r["type"] == typ and r["domain"] == "D7"]
            a = aggregate(sub, ["n"]); ns = sorted(k[0] for k in a)
            exps.append(fit_exponent(ns, [a[(n,)][0] for n in ns])[0])
    m["SortExpMin"], m["SortExpMax"] = tex_num(min(exps)), tex_num(max(exps))
    # Pendiente de n log2 n en el rango medido (referencia del ajuste).
    m["SortExpNlogn"] = tex_num(fit_exponent(ns_all, [n * math.log2(n) for n in ns_all])[0])

    # Constantes ocultas: razón frente a std::sort, n máximo, aleatorio D7.
    base = med("std_sort", n_max, "aleatorio", "D7")
    for algo, nm in (("quick_sort", "Quick"), ("merge_sort", "Merge"),
                     ("patience_sort", "Patience")):
        m[f"SortRatio{nm}Std"] = tex_num(med(algo, n_max, "aleatorio", "D7") / base)
    m["SortWorstOverBest"] = tex_num(
        max(med(a, n_max, "aleatorio", "D7") for a in ALGOS) /
        min(med(a, n_max, "aleatorio", "D7") for a in ALGOS), 1)

    # Costo por operación de std::sort (ns / (n log2 n)), aleatorio D7.
    ns_small = med("std_sort", n_small, "aleatorio", "D7") * 1e6 / (n_small * math.log2(n_small))
    ns_mid = med("std_sort", n_mid, "aleatorio", "D7") * 1e6 / (n_mid * math.log2(n_mid))
    m["SortStdNsSmall"], m["SortStdNsMid"] = tex_num(ns_small), tex_num(ns_mid)
    m["SortStdNsFactor"] = tex_num(ns_mid / ns_small, 1)
    m["SortStdTenNs"] = tex_num(med("std_sort", 10, "aleatorio", "D7") * 1e6, 0)

    # Sensibilidad al orden inicial: aleatorio / mejor de las dos ordenadas.
    for algo, nm in (("std_sort", "Std"), ("quick_sort", "Quick"), ("merge_sort", "Merge")):
        best = min(med(algo, n_max, t, "D7") for t in ("ascendente", "descendente"))
        m[f"SortOrderGain{nm}"] = tex_num(med(algo, n_max, "aleatorio", "D7") / best, 1)
    # Sensibilidad al dominio: D7 / D1 con entrada aleatoria.
    for algo, nm in (("std_sort", "Std"), ("patience_sort", "Patience")):
        m[f"SortDomainFactor{nm}"] = tex_num(
            med(algo, n_max, "aleatorio", "D7") / med(algo, n_max, "aleatorio", "D1"), 1)

    # Patience sort: mejor caso, caso teóricamente peor y peor caso medido.
    pat_desc = med("patience_sort", n_max, "descendente", "D7")
    pat_asc = med("patience_sort", n_max, "ascendente", "D7")
    pat_rand = med("patience_sort", n_max, "aleatorio", "D7")
    m["SortPatDescMs"] = tex_num(pat_desc, 1)
    m["SortStdDescMs"] = tex_num(med("std_sort", n_max, "descendente", "D7"), 1)
    m["SortPatAscMs"] = tex_num(pat_asc, 0)
    m["SortPatRandMs"] = tex_num(pat_rand, 0)
    m["SortPatRandOverAsc"] = tex_num(pat_rand / pat_asc, 1)
    m["SortPatWorstBest"] = tex_num(pat_rand / pat_desc, 1)
    others = []
    for algo in ("std_sort", "merge_sort", "quick_sort"):
        v = [med(algo, n_max, t, "D7") for t in TYPES]
        others.append(max(v) / min(v))
    m["SortOthersWorstBestMin"] = tex_num(min(others), 1)
    m["SortOthersWorstBestMax"] = tex_num(max(others), 1)
    # Pilas esperadas con entrada ascendente D7: valores distintos entre n
    # extracciones con reemplazo de {0..n} = n(1 - 1/e), en millones.
    m["SortPatPilesTheory"] = tex_num(n_max * (1 - math.exp(-1)) / 1e6, 1)
    m["SortPatPilesRandom"] = tex_num(2 * math.sqrt(n_max), 0)   # ~2 sqrt(n)

    # Memoria: pico de patience sort y su relación con el arreglo (4n bytes).
    peak_pat = max(r["heap"] for r in rows if r["algorithm"] == "patience_sort" and r["n"] == n_max)
    m["SortPatMemWorst"] = human_bytes(peak_pat).replace(" ", "~")
    m["SortPatMemWorstOverArray"] = tex_num(peak_pat / (4.0 * n_max), 1)
    m["SortNMaxMiB"] = tex_num(4.0 * n_max / 2 ** 20, 1)

    lines = [TEX_IDENT.replace("ARCHIVO GENERADO", "MACROS NUMERICAS. ARCHIVO GENERADO")]
    for k in sorted(m):
        lines.append(f"\\newcommand{{\\{k}}}{{{m[k]}}}\n")
    path = os.path.join(out_dir, "numbers_sorting.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(
        description="Genera los graficos y tablas del experimento de ordenamiento.")
    p.add_argument("--csv", default=DEFAULT_CSV, help="CSV de mediciones")
    p.add_argument("--out", default=DEFAULT_PLOTS, help="directorio de graficos")
    p.add_argument("--tables", default=DEFAULT_TABLES,
                   help="directorio de las tablas LaTeX")
    args = p.parse_args(argv)

    rows = load(args.csv)
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(args.tables, exist_ok=True)

    incorrectas = sum(1 for r in rows if r["correct"] == 0)
    if incorrectas:
        print(f"AVISO: {incorrectas} mediciones marcadas como incorrectas en el CSV.")

    print(f"Leidas {len(rows)} mediciones de {args.csv}")
    generated = []
    for fn in (fig_time_vs_n, fig_time_random, fig_normalized, fig_memory,
               fig_input_type_effect, fig_speedup):
        path = fn(rows, args.out)
        if path:
            generated.append(path)
    for fn in (table_time, table_memory, table_exponents, numbers_tex):
        generated.append(fn(rows, args.tables))

    print("\nArchivos generados:")
    for g in generated:
        print("  " + os.path.relpath(g, PROJECT_DIR).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
