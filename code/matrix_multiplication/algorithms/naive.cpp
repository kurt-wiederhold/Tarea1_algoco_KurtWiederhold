/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Multiplicación clásica: C[i][j] = sum_k A[i][k]·B[k][j], tres bucles i-j-k.
 * Complejidad: Θ(n³) en tiempo, independiente de los datos (una matriz
 * diagonal cuesta lo mismo que una densa); Θ(1) de memoria auxiliar además
 * de la matriz resultado.
 *
 * Se deja el orden de bucles "de libro", que recorre B por columnas con un
 * salto de 8n bytes; el efecto de eso sobre la caché es justamente parte de
 * lo que se estudia en el informe.
 *
 * Referencias:
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., sección 4.2.
 * - Golub y Van Loan, Matrix Computations, 4.ª ed., sección 1.1.
 *
 * Implementación propia.
 */

#include "matrix.hpp"

#include <cstddef>

// Documentada en matrix.hpp.
Matrix naiveMultiply(const Matrix& A, const Matrix& B) {
    const std::size_t n = A.n;
    Matrix C(n);

    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            long long sum = 0;
            for (std::size_t k = 0; k < n; ++k) {
                sum += A.data[i * n + k] * B.data[k * n + j];
            }
            C.data[i * n + j] = sum;
        }
    }
    return C;
}
