/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Programa principal del experimento de ordenamiento. Recorre los archivos
 * {n}_{t}_{d}_{m}.txt de data/array_input/, ejecuta los cuatro algoritmos
 * sobre cada uno, verifica el resultado contra std::sort, escribe el arreglo
 * ordenado en data/array_output/ y agrega una fila por medición al CSV.
 *
 * Cómo se mide:
 * - Solo se cronometra la llamada al algoritmo; la lectura, la copia, la
 *   verificación y la escritura quedan fuera (para n = 10^7 la E/S tarda más
 *   que ordenar).
 * - Cada caso se repite varias veces (15/7/3 según n) y se guarda cada
 *   repetición; el script de gráficos calcula la mediana.
 * - Para n pequeño una ejecución dura menos que la resolución del reloj, así
 *   que se ordenan `batch` copias dentro de la región medida y se divide el
 *   total. El tamaño del lote queda en el CSV.
 * - La memoria se mide en una ejecución aparte, sin lote, para que no se
 *   solapen las asignaciones de una llamada con la siguiente.
 *
 * Referencias:
 * - McGeoch, A Guide to Experimental Algorithmics, CUP 2012, caps. 1 y 3.
 * - Hales, "An Introduction to Replicability in Computer Science Research", 2017.
 * - cppreference, std::filesystem::directory_iterator.
 *
 * Implementación propia.
 */

#include "algorithms/algorithms.hpp"
#include "../common/benchmark.hpp"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// Caso de prueba deducido del nombre del archivo.
struct TestCase {
    fs::path     path;    // ruta completa del archivo de entrada
    std::string  base;    // "{n}_{t}_{d}_{m}"
    long long    n = 0;   // cantidad de elementos declarada en el nombre
    std::string  type;    // ascendente | descendente | aleatorio
    std::string  domain;  // D1 | D7
    std::string  sample;  // a | b | c
};

/**
 * Función: Descompone un nombre "{n}_{t}_{d}_{m}.txt" en sus campos.
 * Parámetros:
 * - p: ruta del archivo de entrada.
 * - out: caso de prueba que se completa.
 * Retorno: false si el nombre no sigue el patrón (se ignora el archivo).
 */
static bool parseCaseName(const fs::path& p, TestCase& out) {
    const std::string stem = p.stem().string();   // sin ".txt"

    std::vector<std::string> parts;
    std::string current;
    for (const char c : stem) {
        if (c == '_') { parts.push_back(current); current.clear(); }
        else          { current.push_back(c); }
    }
    parts.push_back(current);

    if (parts.size() != 4) return false;                 // descarta a.txt, etc.
    if (parts[0].empty()) return false;
    for (const char c : parts[0]) if (!std::isdigit(static_cast<unsigned char>(c))) return false;

    out.path   = p;
    out.base   = stem;
    out.n      = std::strtoll(parts[0].c_str(), nullptr, 10);
    out.type   = parts[1];
    out.domain = parts[2];
    out.sample = parts[3];
    return true;
}

/**
 * Función: Lee un arreglo de enteros separados por espacios.
 * Parámetros:
 * - path: archivo de entrada.
 * - out: vector donde se dejan los valores.
 * Retorno: false si el archivo no se pudo abrir.
 *
 * Se lee el archivo completo a un búfer y se parsea a mano: con n = 10^7,
 * `ifstream >> int` tarda decenas de segundos por archivo. De todos modos la
 * lectura queda fuera del cronómetro.
 */
static bool readArray(const fs::path& path, std::vector<int>& out) {
    std::FILE* f = std::fopen(path.string().c_str(), "rb");
    if (f == nullptr) return false;

    std::fseek(f, 0, SEEK_END);
    const long long size = std::ftell(f);
    std::fseek(f, 0, SEEK_SET);
    if (size < 0) { std::fclose(f); return false; }

    std::vector<char> buffer(static_cast<std::size_t>(size) + 1);
    const std::size_t got = std::fread(buffer.data(), 1, static_cast<std::size_t>(size), f);
    buffer[got] = '\0';
    std::fclose(f);

    out.clear();
    // Cota superior del número de enteros: sirve para reservar una sola vez.
    out.reserve(static_cast<std::size_t>(size) / 2 + 1);

    const char* p = buffer.data();
    const char* end = buffer.data() + got;
    while (p < end) {
        while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) ++p;
        if (p >= end) break;

        bool negative = false;
        if (*p == '-') { negative = true; ++p; }

        long long value = 0;
        bool any = false;
        while (p < end && *p >= '0' && *p <= '9') {
            value = value * 10 + (*p - '0');
            ++p;
            any = true;
        }
        if (any) out.push_back(static_cast<int>(negative ? -value : value));
        else     ++p;  // carácter inesperado: se ignora
    }
    out.shrink_to_fit();
    return true;
}

/**
 * Función: Escribe el arreglo ordenado en el mismo formato de la entrada
 * (una línea, valores separados por espacios).
 * Parámetros:
 * - path: archivo de salida.
 * - arr: arreglo a escribir.
 * Retorno: false si el archivo no se pudo crear.
 */
static bool writeArray(const fs::path& path, const std::vector<int>& arr) {
    std::FILE* f = std::fopen(path.string().c_str(), "wb");
    if (f == nullptr) return false;

    std::string out;
    out.reserve(arr.size() * 4 + 16);
    char tmp[16];
    for (std::size_t i = 0; i < arr.size(); ++i) {
        if (i != 0) out.push_back(' ');
        const int len = std::snprintf(tmp, sizeof(tmp), "%d", arr[i]);
        out.append(tmp, static_cast<std::size_t>(len));
        if (out.size() > (1u << 22)) {              // vaciado por bloques de 4 MiB
            std::fwrite(out.data(), 1, out.size(), f);
            out.clear();
        }
    }
    out.push_back('\n');
    std::fwrite(out.data(), 1, out.size(), f);
    std::fclose(f);
    return true;
}

// Algoritmos a medir: nombre para el CSV y puntero a la función.
struct Algorithm {
    const char* name;
    std::vector<int> (*run)(std::vector<int>&);
};

static const Algorithm kAlgorithms[] = {
    {"std_sort",      &sortArray},
    {"merge_sort",    &mergeSort},
    {"quick_sort",    &quickSort},
    {"patience_sort", &patienceSort},
};
static constexpr int kNumAlgorithms =
    static_cast<int>(sizeof(kAlgorithms) / sizeof(kAlgorithms[0]));

// Opciones de línea de comandos (ver --help).
struct Options {
    fs::path inputDir     = "data/array_input";
    fs::path outputDir    = "data/array_output";
    fs::path measurements = "data/measurements/sorting_measurements.csv";
    int      reps         = 0;          // 0 = automático según n
    int      batch        = 0;          // 0 = automático según n
    long long maxN        = -1;         // -1 = sin límite
    // Por omisión se escribe la salida de todos los casos, como pide el anexo
    // A.1. --max-output-n permite acotarlo cuando solo interesan las mediciones
    // (los 18 casos con n = 10^7 producen ~1,5 GB de texto).
    long long maxOutputN  = -1;         // -1 = escribir siempre
    bool     append       = false;      // agregar al CSV en vez de sobrescribirlo
    bool     quiet        = false;
};

/**
 * Función: Repeticiones por caso según su tamaño.
 * Parámetros: n es el tamaño del arreglo; opt puede fijar un valor explícito.
 * Retorno: 15, 7 o 3 (o el valor de --reps).
 */
static int repsForSize(long long n, const Options& opt) {
    if (opt.reps > 0) return opt.reps;
    if (n <= 1000)    return 15;
    if (n <= 100000)  return 7;
    return 3;
}

/**
 * Función: Ejecuciones agrupadas en una misma región cronometrada, calibradas
 * para que cada medición dure del orden del milisegundo.
 * Parámetros: n es el tamaño del arreglo; opt puede fijar un valor explícito.
 * Retorno: Tamaño del lote.
 */
static int batchForSize(long long n, const Options& opt) {
    if (opt.batch > 0) return opt.batch;
    if (n <= 100)     return 2000;
    if (n <= 10000)   return 200;
    if (n <= 1000000) return 5;
    return 1;
}

static void printHelp(const char* prog) {
    std::cout <<
        "Uso: " << prog << " [opciones]\n\n"
        "Ejecuta los cuatro algoritmos de ordenamiento sobre todos los casos de\n"
        "prueba de data/array_input/ y registra tiempo y memoria en un CSV.\n\n"
        "Opciones:\n"
        "  --input-dir DIR      Directorio de entradas      (por omision data/array_input)\n"
        "  --output-dir DIR     Directorio de salidas       (por omision data/array_output)\n"
        "  --measurements FILE  CSV de mediciones           (por omision data/measurements/sorting_measurements.csv)\n"
        "  --reps N             Repeticiones fijas por caso (por omision: 15/7/3 segun n)\n"
        "  --batch N            Ejecuciones por region cronometrada (por omision: automatico)\n"
        "  --max-n N            Omite los casos con n > N\n"
        "  --max-output-n N     No escribe el archivo _out.txt si n > N (por omision: sin limite)\n"
        "  --no-output          Equivale a --max-output-n 0\n"
        "  --append             Agrega al CSV en lugar de sobrescribirlo\n"
        "  --quiet              Reduce la salida por consola\n"
        "  -h, --help           Muestra esta ayuda\n";
}

/**
 * Función: Interpreta los argumentos de línea de comandos.
 * Parámetros: argc y argv de main; opt recibe los valores.
 * Retorno: false ante una opción desconocida.
 */
static bool parseOptions(int argc, char** argv, Options& opt) {
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto needValue = [&](const char* name) -> const char* {
            if (i + 1 >= argc) {
                std::cerr << "Error: la opcion " << name << " requiere un valor.\n";
                std::exit(2);
            }
            return argv[++i];
        };

        if      (a == "-h" || a == "--help") { printHelp(argv[0]); std::exit(0); }
        else if (a == "--input-dir")     opt.inputDir     = needValue("--input-dir");
        else if (a == "--output-dir")    opt.outputDir    = needValue("--output-dir");
        else if (a == "--measurements")  opt.measurements = needValue("--measurements");
        else if (a == "--reps")          opt.reps         = std::atoi(needValue("--reps"));
        else if (a == "--batch")         opt.batch        = std::atoi(needValue("--batch"));
        else if (a == "--max-n")         opt.maxN         = std::strtoll(needValue("--max-n"), nullptr, 10);
        else if (a == "--max-output-n")  opt.maxOutputN   = std::strtoll(needValue("--max-output-n"), nullptr, 10);
        else if (a == "--no-output")     opt.maxOutputN   = 0;
        else if (a == "--append")        opt.append       = true;
        else if (a == "--quiet")         opt.quiet        = true;
        else {
            std::cerr << "Error: opcion desconocida '" << a << "'. Use --help.\n";
            return false;
        }
    }
    return true;
}

int main(int argc, char** argv) {
    Options opt;
    if (!parseOptions(argc, argv, opt)) return 2;

    std::error_code ec;
    if (!fs::exists(opt.inputDir)) {
        std::cerr << "Error: no existe el directorio de entrada '" << opt.inputDir.string()
                  << "'.\n       Genere los casos con: make data  (o python scripts/array_generator.py)\n";
        return 1;
    }
    fs::create_directories(opt.outputDir, ec);
    fs::create_directories(opt.measurements.parent_path(), ec);

    // Los casos se ordenan por n, tipo, dominio y muestra: el CSV queda
    // legible y los casos baratos van primero.
    std::vector<TestCase> cases;
    for (const auto& entry : fs::directory_iterator(opt.inputDir)) {
        if (!entry.is_regular_file()) continue;
        if (entry.path().extension() != ".txt") continue;
        TestCase tc;
        if (!parseCaseName(entry.path(), tc)) continue;
        if (opt.maxN >= 0 && tc.n > opt.maxN) continue;
        cases.push_back(tc);
    }
    std::sort(cases.begin(), cases.end(), [](const TestCase& a, const TestCase& b) {
        if (a.n != b.n)         return a.n < b.n;
        if (a.type != b.type)   return a.type < b.type;
        if (a.domain != b.domain) return a.domain < b.domain;
        return a.sample < b.sample;
    });

    if (cases.empty()) {
        std::cerr << "Error: no se encontro ningun caso de prueba con el patron "
                     "{n}_{t}_{d}_{m}.txt en '" << opt.inputDir.string() << "'.\n";
        return 1;
    }

    std::ofstream csv(opt.measurements,
                      opt.append ? (std::ios::out | std::ios::app) : std::ios::out);
    if (!csv) {
        std::cerr << "Error: no se pudo abrir '" << opt.measurements.string() << "'.\n";
        return 1;
    }
    if (!opt.append) {
        csv << "algorithm,n,type,domain,sample,rep,batch,time_ms,peak_heap_bytes,"
               "peak_rss_bytes,correct\n";
    }

    if (!opt.quiet) {
        std::cout << "== Experimento de ordenamiento ==\n"
                  << "Casos de prueba : " << cases.size() << "\n"
                  << "Algoritmos      : " << kNumAlgorithms << "\n"
                  << "Mediciones      : " << opt.measurements.string() << "\n\n";
    }

    std::size_t caseIndex = 0;
    int failures = 0;

    for (const TestCase& tc : cases) {
        ++caseIndex;

        std::vector<int> original;
        if (!readArray(tc.path, original)) {
            std::cerr << "  [!] No se pudo leer " << tc.path.string() << "\n";
            continue;
        }
        if (static_cast<long long>(original.size()) != tc.n && !opt.quiet) {
            std::cerr << "  [!] Aviso: " << tc.base << " declara n=" << tc.n
                      << " pero contiene " << original.size() << " elementos.\n";
        }

        const long long realN = static_cast<long long>(original.size());
        const int reps  = repsForSize(realN, opt);
        const int batch = batchForSize(realN, opt);

        // Referencia de correctitud: el resultado de std::sort.
        std::vector<int> reference = original;
        std::sort(reference.begin(), reference.end());

        if (!opt.quiet) {
            std::cout << "[" << caseIndex << "/" << cases.size() << "] " << tc.base
                      << "  (n=" << original.size() << ", reps=" << reps
                      << ", batch=" << batch << ")\n";
        }

        for (int ai = 0; ai < kNumAlgorithms; ++ai) {
            const Algorithm& algo = kAlgorithms[ai];
            double bestMs = 0.0;
            bool   correct = true;

            // Memoria: una sola ejecución aislada. El consumo es determinista,
            // así que el mismo valor se replica en todas las repeticiones.
            std::size_t heap = 0;
            std::size_t rss  = 0;
            {
                std::vector<int> memWork = original;
                bench::resetHeapPeak();
                algo.run(memWork);
                heap = bench::peakHeapBytes();
                rss  = bench::peakResidentBytes();
            }

            // Tiempo: `reps` mediciones, cada una sobre un lote.
            for (int rep = 1; rep <= reps; ++rep) {
                // Copias frescas preparadas fuera de la región cronometrada.
                std::vector<std::vector<int>> work(
                    static_cast<std::size_t>(batch), original);

                bench::Timer timer;
                for (int b = 0; b < batch; ++b) {
                    algo.run(work[static_cast<std::size_t>(b)]);
                }
                const double ms = timer.elapsedMs() / batch;

                const bool ok = (work[0] == reference);
                if (!ok) correct = false;

                csv << algo.name << ',' << original.size() << ',' << tc.type << ','
                    << tc.domain << ',' << tc.sample << ',' << rep << ',' << batch << ','
                    << ms << ',' << heap << ',' << rss << ',' << (ok ? 1 : 0) << '\n';

                if (rep == 1 || ms < bestMs) bestMs = ms;

                // Se conserva una sola copia de salida por caso (los cuatro
                // algoritmos producen el mismo arreglo, ya verificado).
                if (ai == 0 && rep == 1 && ok &&
                    (opt.maxOutputN < 0 || realN <= opt.maxOutputN)) {
                    const fs::path outPath = opt.outputDir / (tc.base + "_out.txt");
                    if (!writeArray(outPath, work[0])) {
                        std::cerr << "  [!] No se pudo escribir " << outPath.string() << "\n";
                    }
                }
            }

            if (!correct) ++failures;
            if (!opt.quiet) {
                std::printf("      %-14s  %10.3f ms  %s\n",
                            algo.name, bestMs, correct ? "ok" : "INCORRECTO");
            }
        }
        csv.flush();
    }

    csv.close();

    if (!opt.quiet) {
        std::cout << "\nListo. Mediciones en " << opt.measurements.string() << "\n";
        if (opt.maxOutputN < 0) {
            std::cout << "Salidas ordenadas en " << opt.outputDir.string() << ".\n";
        } else if (opt.maxOutputN > 0) {
            std::cout << "Salidas ordenadas en " << opt.outputDir.string()
                      << " (solo para n <= " << opt.maxOutputN << ").\n";
        }
    }
    if (failures > 0) {
        std::cerr << "ATENCION: " << failures
                  << " combinaciones algoritmo/caso produjeron un resultado incorrecto.\n";
        return 1;
    }
    return 0;
}
