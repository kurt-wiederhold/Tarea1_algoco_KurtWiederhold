/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Programa principal del experimento de multiplicación de matrices. Busca
 * los pares {n}_{t}_{d}_{m}_1.txt / _2.txt en data/matrix_input/, ejecuta el
 * método clásico y Strassen sobre cada par, verifica que Strassen coincida
 * coeficiente a coeficiente con el clásico, escribe el producto en
 * data/matrix_output/ y agrega una fila por medición al CSV.
 *
 * La metodología es la misma de sorting.cpp: solo se cronometra la llamada
 * al algoritmo, se repite cada caso varias veces, para n pequeño se encadenan
 * `batch` productos en la región medida, y la memoria se mide en una
 * ejecución aparte. Como el contador de heap se reinicia justo antes de cada
 * llamada, para el clásico mide esencialmente la matriz resultado y para
 * Strassen además sus bloques temporales.
 *
 * Referencias:
 * - Strassen, "Gaussian elimination is not optimal", Numer. Math. 13, 1969.
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., sección 4.2.
 * - McGeoch, A Guide to Experimental Algorithmics, CUP 2012.
 * - cppreference, std::filesystem::directory_iterator.
 *
 * Implementación propia.
 */

#include "algorithms/matrix.hpp"
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

// Caso de prueba: un par de matrices con el mismo nombre base.
struct TestCase {
    fs::path    pathA;    // {base}_1.txt
    fs::path    pathB;    // {base}_2.txt
    std::string base;     // "{n}_{t}_{d}_{m}"
    long long   n = 0;    // dimensión declarada en el nombre
    std::string type;     // dispersa | diagonal | densa
    std::string domain;   // D0 | D10
    std::string sample;   // a | b | c
};

/**
 * Función: Descompone un nombre base "{n}_{t}_{d}_{m}" (sin el sufijo _1/_2).
 * Parámetros:
 * - base: nombre base del par.
 * - out: caso de prueba que se completa.
 * Retorno: false si el nombre no sigue el patrón.
 */
static bool parseCaseBase(const std::string& base, TestCase& out) {
    std::vector<std::string> parts;
    std::string current;
    for (const char c : base) {
        if (c == '_') { parts.push_back(current); current.clear(); }
        else          { current.push_back(c); }
    }
    parts.push_back(current);

    if (parts.size() != 4) return false;
    if (parts[0].empty()) return false;
    for (const char c : parts[0]) if (!std::isdigit(static_cast<unsigned char>(c))) return false;

    out.base   = base;
    out.n      = std::strtoll(parts[0].c_str(), nullptr, 10);
    out.type   = parts[1];
    out.domain = parts[2];
    out.sample = parts[3];
    return true;
}

/**
 * Función: Lee una matriz cuadrada (una fila por línea, valores separados
 * por espacios). La dimensión se deduce de la cantidad de números leídos.
 * Parámetros:
 * - path: archivo de entrada.
 * - out: matriz que se llena.
 * Retorno: false si no se pudo abrir o el archivo no es cuadrado.
 *
 * Igual que en sorting.cpp, se lee todo el archivo y se parsea a mano por
 * velocidad; la lectura queda fuera del cronómetro.
 */
static bool readMatrix(const fs::path& path, Matrix& out) {
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

    std::vector<long long> values;
    values.reserve(static_cast<std::size_t>(size) / 2 + 1);

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
        if (any) values.push_back(negative ? -value : value);
        else     ++p;
    }

    // Dimensión: raíz entera de la cantidad de coeficientes.
    std::size_t n = 0;
    while ((n + 1) * (n + 1) <= values.size()) ++n;
    if (n == 0 || n * n != values.size()) return false;   // archivo no cuadrado

    out.n = n;
    out.data = std::move(values);
    return true;
}

/**
 * Función: Escribe la matriz en el formato de los archivos de entrada.
 * Parámetros:
 * - path: archivo de salida.
 * - M: matriz a escribir.
 * Retorno: false si el archivo no se pudo crear.
 */
static bool writeMatrix(const fs::path& path, const Matrix& M) {
    std::FILE* f = std::fopen(path.string().c_str(), "wb");
    if (f == nullptr) return false;

    std::string out;
    out.reserve(M.n * 8 + 16);
    char tmp[32];
    for (std::size_t i = 0; i < M.n; ++i) {
        for (std::size_t j = 0; j < M.n; ++j) {
            if (j != 0) out.push_back(' ');
            const int len = std::snprintf(tmp, sizeof(tmp), "%lld", M(i, j));
            out.append(tmp, static_cast<std::size_t>(len));
        }
        out.push_back('\n');
        if (out.size() > (1u << 22)) {            // vaciado por bloques de 4 MiB
            std::fwrite(out.data(), 1, out.size(), f);
            out.clear();
        }
    }
    std::fwrite(out.data(), 1, out.size(), f);
    std::fclose(f);
    return true;
}

// Algoritmos a medir: nombre para el CSV y puntero a la función.
struct Algorithm {
    const char* name;
    Matrix (*run)(const Matrix&, const Matrix&);
};

static const Algorithm kAlgorithms[] = {
    {"naive",    &naiveMultiply},
    {"strassen", &strassenMultiply},
};
static constexpr int kNumAlgorithms =
    static_cast<int>(sizeof(kAlgorithms) / sizeof(kAlgorithms[0]));

// Opciones de línea de comandos (ver --help).
struct Options {
    fs::path  inputDir     = "data/matrix_input";
    fs::path  outputDir    = "data/matrix_output";
    fs::path  measurements = "data/measurements/matrix_multiplication_measurements.csv";
    int       reps         = 0;      // 0 = automático según n
    int       batch        = 0;      // 0 = automático según n
    long long maxN         = -1;     // -1 = sin límite
    long long maxOutputN   = -1;     // -1 = escribir siempre
    long long cutoff       = 64;     // umbral de corte de Strassen
    bool      append       = false;
    bool      quiet        = false;
};

/**
 * Función: Repeticiones por caso según la dimensión.
 * Parámetros: n es la dimensión; opt puede fijar un valor explícito.
 * Retorno: 15, 7 o 3 (o el valor de --reps).
 */
static int repsForSize(long long n, const Options& opt) {
    if (opt.reps > 0) return opt.reps;
    if (n <= 64)  return 15;
    if (n <= 256) return 7;
    return 3;
}

/**
 * Función: Productos encadenados en una misma región cronometrada, para que
 * cada medición supere con holgura la resolución del reloj.
 * Parámetros: n es la dimensión; opt puede fijar un valor explícito.
 * Retorno: Tamaño del lote.
 */
static int batchForSize(long long n, const Options& opt) {
    if (opt.batch > 0) return opt.batch;
    if (n <= 32)  return 200;
    if (n <= 128) return 20;
    if (n <= 512) return 3;
    return 1;
}

static void printHelp(const char* prog) {
    std::cout <<
        "Uso: " << prog << " [opciones]\n\n"
        "Multiplica todos los pares de matrices de data/matrix_input/ con los\n"
        "algoritmos naive y Strassen, y registra tiempo y memoria en un CSV.\n\n"
        "Opciones:\n"
        "  --input-dir DIR      Directorio de entradas  (por omision data/matrix_input)\n"
        "  --output-dir DIR     Directorio de salidas   (por omision data/matrix_output)\n"
        "  --measurements FILE  CSV de mediciones\n"
        "  --reps N             Repeticiones fijas por caso (por omision: 15/7/3 segun n)\n"
        "  --batch N            Productos por region cronometrada (por omision: automatico)\n"
        "  --max-n N            Omite los casos con n > N\n"
        "  --max-output-n N     No escribe el archivo _out.txt si n > N\n"
        "  --no-output          Equivale a --max-output-n 0\n"
        "  --cutoff N           Umbral de corte de Strassen (por omision 64)\n"
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
        else if (a == "--cutoff")        opt.cutoff       = std::strtoll(needValue("--cutoff"), nullptr, 10);
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

    if (opt.cutoff < 1) opt.cutoff = 1;
    strassenCutoff = static_cast<std::size_t>(opt.cutoff);

    std::error_code ec;
    if (!fs::exists(opt.inputDir)) {
        std::cerr << "Error: no existe el directorio de entrada '" << opt.inputDir.string()
                  << "'.\n       Genere los casos con: make data  (o python scripts/matrix_generator.py)\n";
        return 1;
    }
    fs::create_directories(opt.outputDir, ec);
    fs::create_directories(opt.measurements.parent_path(), ec);

    // Se buscan los archivos "_1.txt" y se exige que exista el "_2.txt".
    std::vector<TestCase> cases;
    for (const auto& entry : fs::directory_iterator(opt.inputDir)) {
        if (!entry.is_regular_file()) continue;
        if (entry.path().extension() != ".txt") continue;

        const std::string stem = entry.path().stem().string();
        if (stem.size() < 3 || stem.compare(stem.size() - 2, 2, "_1") != 0) continue;

        const std::string base = stem.substr(0, stem.size() - 2);
        TestCase tc;
        if (!parseCaseBase(base, tc)) continue;

        tc.pathA = entry.path();
        tc.pathB = entry.path().parent_path() / (base + "_2.txt");
        if (!fs::exists(tc.pathB)) {
            std::cerr << "  [!] Falta la segunda matriz de " << base << ", se omite el caso.\n";
            continue;
        }
        if (opt.maxN >= 0 && tc.n > opt.maxN) continue;
        cases.push_back(tc);
    }
    std::sort(cases.begin(), cases.end(), [](const TestCase& a, const TestCase& b) {
        if (a.n != b.n)           return a.n < b.n;
        if (a.type != b.type)     return a.type < b.type;
        if (a.domain != b.domain) return a.domain < b.domain;
        return a.sample < b.sample;
    });

    if (cases.empty()) {
        std::cerr << "Error: no se encontro ningun par de matrices con el patron "
                     "{n}_{t}_{d}_{m}_1.txt / _2.txt en '" << opt.inputDir.string() << "'.\n";
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
               "peak_rss_bytes,cutoff,correct\n";
    }

    if (!opt.quiet) {
        std::cout << "== Experimento de multiplicacion de matrices ==\n"
                  << "Casos de prueba   : " << cases.size() << "\n"
                  << "Algoritmos        : " << kNumAlgorithms << "\n"
                  << "Umbral de Strassen: " << strassenCutoff << "\n"
                  << "Mediciones        : " << opt.measurements.string() << "\n\n";
    }

    std::size_t caseIndex = 0;
    int failures = 0;

    for (const TestCase& tc : cases) {
        ++caseIndex;

        Matrix A, B;
        if (!readMatrix(tc.pathA, A) || !readMatrix(tc.pathB, B)) {
            std::cerr << "  [!] No se pudieron leer las matrices de " << tc.base << "\n";
            continue;
        }
        if (A.n != B.n) {
            std::cerr << "  [!] Dimensiones incompatibles en " << tc.base << "\n";
            continue;
        }

        const int reps  = repsForSize(static_cast<long long>(A.n), opt);
        const int batch = batchForSize(static_cast<long long>(A.n), opt);

        // Referencia de correctitud: el producto clásico.
        const Matrix reference = naiveMultiply(A, B);

        if (!opt.quiet) {
            std::cout << "[" << caseIndex << "/" << cases.size() << "] " << tc.base
                      << "  (n=" << A.n << ", reps=" << reps
                      << ", batch=" << batch << ")\n";
        }

        for (int ai = 0; ai < kNumAlgorithms; ++ai) {
            const Algorithm& algo = kAlgorithms[ai];
            double bestMs = 0.0;
            bool   correct = true;

            // Memoria: una sola ejecución aislada, igual que en ordenamiento.
            std::size_t heap = 0;
            std::size_t rss  = 0;
            {
                bench::resetHeapPeak();
                Matrix memC = algo.run(A, B);
                heap = bench::peakHeapBytes();
                rss  = bench::peakResidentBytes();
            }

            // Tiempo: `reps` mediciones, cada una sobre un lote.
            for (int rep = 1; rep <= reps; ++rep) {
                Matrix C;
                bench::Timer timer;
                for (int b = 0; b < batch; ++b) {
                    C = algo.run(A, B);
                }
                const double ms = timer.elapsedMs() / batch;

                const bool ok = (C == reference);
                if (!ok) correct = false;

                csv << algo.name << ',' << A.n << ',' << tc.type << ','
                    << tc.domain << ',' << tc.sample << ',' << rep << ',' << batch << ','
                    << ms << ',' << heap << ',' << rss << ',' << strassenCutoff
                    << ',' << (ok ? 1 : 0) << '\n';

                if (rep == 1 || ms < bestMs) bestMs = ms;

                // Se conserva una sola copia de salida por caso.
                if (ai == 0 && rep == 1 && ok &&
                    (opt.maxOutputN < 0 || static_cast<long long>(A.n) <= opt.maxOutputN)) {
                    const fs::path outPath = opt.outputDir / (tc.base + "_out.txt");
                    if (!writeMatrix(outPath, C)) {
                        std::cerr << "  [!] No se pudo escribir " << outPath.string() << "\n";
                    }
                }
            }

            if (!correct) ++failures;
            if (!opt.quiet) {
                std::printf("      %-10s  %12.3f ms  %s\n",
                            algo.name, bestMs, correct ? "ok" : "INCORRECTO");
            }
        }
        csv.flush();
    }

    csv.close();

    if (!opt.quiet) {
        std::cout << "\nListo. Mediciones en " << opt.measurements.string() << "\n";
    }
    if (failures > 0) {
        std::cerr << "ATENCION: " << failures
                  << " combinaciones algoritmo/caso produjeron un resultado incorrecto.\n";
        return 1;
    }
    return 0;
}
