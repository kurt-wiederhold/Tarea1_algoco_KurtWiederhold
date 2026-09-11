/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Tipo Matrix (cuadrada, almacenamiento plano por filas) y declaraciones de
 * los dos algoritmos de multiplicación del experimento.
 *
 * Se usa un único vector de n·n en vez de vector<vector<...>> para que las
 * filas queden contiguas en memoria; con n = 1024 la indirección por fila
 * distorsionaría la comparación entre los dos algoritmos.
 *
 * Los coeficientes son long long. Con los dominios del enunciado ({0,1} y
 * {0..9}) un int bastaría (el producto está acotado por 9·9·1024), pero así
 * no hay ningún riesgo de desbordamiento en los sumandos intermedios de
 * Strassen y la complejidad no cambia.
 *
 * Referencias:
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., sección 4.2.
 * - Drepper, What Every Programmer Should Know About Memory, 2007, §6.2.1.
 *
 * Implementación propia.
 */

#ifndef MATRIX_HPP
#define MATRIX_HPP

#include <cstddef>
#include <vector>

struct Matrix {
    std::size_t n = 0;              // dimensión (la matriz es n x n)
    std::vector<long long> data;    // n*n coeficientes en orden por filas

    Matrix() = default;

    /**
     * Función: Construye una matriz dim x dim llena de ceros.
     * Parámetros: dim es la dimensión.
     */
    explicit Matrix(std::size_t dim) : n(dim), data(dim * dim, 0) {}

    /**
     * Función: Acceso al coeficiente (i, j) por filas.
     * Parámetros: i es la fila y j la columna, ambas desde 0.
     * Retorno: Referencia al coeficiente.
     */
    inline long long&       operator()(std::size_t i, std::size_t j)       { return data[i * n + j]; }
    inline const long long& operator()(std::size_t i, std::size_t j) const { return data[i * n + j]; }

    bool operator==(const Matrix& other) const {
        return n == other.n && data == other.data;
    }
};

/**
 * Función: Multiplicación clásica de tres bucles anidados.
 * Parámetros: A y B son matrices cuadradas de la misma dimensión.
 * Retorno: El producto A·B.
 * Complejidad: Θ(n³) en tiempo; solo la matriz resultado en memoria.
 */
Matrix naiveMultiply(const Matrix& A, const Matrix& B);

/**
 * Función: Multiplicación con el algoritmo de Strassen.
 * Parámetros: A y B son matrices cuadradas de la misma dimensión.
 * Retorno: El producto A·B.
 * Complejidad: Θ(n^log2 7) ≈ Θ(n^2,807) en tiempo, Θ(n²) de memoria auxiliar.
 */
Matrix strassenMultiply(const Matrix& A, const Matrix& B);

// Umbral de corte de Strassen: por debajo de esta dimensión se delega en el
// método clásico. Lo fija el programa principal con --cutoff.
extern std::size_t strassenCutoff;

#endif  // MATRIX_HPP
