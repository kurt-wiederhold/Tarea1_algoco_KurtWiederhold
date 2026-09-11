/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Algoritmo de Strassen: se parten A y B en cuatro bloques y el producto se
 * obtiene con siete multiplicaciones de bloques en vez de ocho, a cambio de
 * 18 sumas/restas:
 *
 *   M1 = (A11 + A22)(B11 + B22)      C11 = M1 + M4 - M5 + M7
 *   M2 = (A21 + A22) B11             C12 = M3 + M5
 *   M3 = A11 (B12 - B22)             C21 = M2 + M4
 *   M4 = A22 (B21 - B11)             C22 = M1 - M2 + M3 + M6
 *   M5 = (A11 + A12) B22
 *   M6 = (A21 - A11)(B11 + B12)
 *   M7 = (A12 - A22)(B21 + B22)
 *
 * Complejidad: T(n) = 7T(n/2) + Θ(n²) = Θ(n^log2 7) ≈ Θ(n^2,807) en tiempo;
 * Θ(n²) de memoria auxiliar (siete productos y dos temporales por nivel).
 *
 * Decisiones:
 * - Umbral de corte (strassenCutoff): bajo esa dimensión se usa el clásico,
 *   porque las sumas y las asignaciones de memoria dominan en bloques
 *   pequeños. Es un parámetro del experimento (--cutoff).
 * - Los bloques se pasan como vistas (puntero + distancia entre filas) para
 *   no copiarlos en cada nivel.
 * - Si n no es potencia de dos se rellena con ceros y se recorta al final;
 *   con los tamaños del enunciado nunca hace falta.
 *
 * Referencias:
 * - Strassen, "Gaussian elimination is not optimal", Numer. Math. 13, 1969.
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., secciones 4.2 y 4.5.
 * - Huss-Lederman et al., "Implementation of Strassen's Algorithm for Matrix
 *   Multiplication", Supercomputing '96 (umbral de corte).
 *
 * Implementación propia a partir de las recurrencias de Strassen y el
 * pseudocódigo de CLRS.
 */

#include "matrix.hpp"

#include <cstddef>
#include <vector>

// Umbral de corte por omisión; el programa principal lo puede cambiar.
std::size_t strassenCutoff = 64;

namespace {

/**
 * Función: Suma dos bloques cuadrados, Z = X + Y.
 * Parámetros:
 * - X: primer bloque.
 * - ldx: distancia entre las filas de X.
 * - Y: segundo bloque.
 * - ldy: distancia entre las filas de Y.
 * - Z: bloque donde se guarda el resultado.
 * - ldz: distancia entre las filas de Z.
 * - n: dimensión de los bloques.
 * Resultado: La suma queda almacenada en Z.
 */
void addBlock(const long long* X, std::size_t ldx,
              const long long* Y, std::size_t ldy,
              long long* Z, std::size_t ldz, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = 0; j < n; ++j)
            Z[i * ldz + j] = X[i * ldx + j] + Y[i * ldy + j];
}

/**
 * Función: Resta dos bloques cuadrados, Z = X - Y.
 * Parámetros: los mismos de addBlock.
 * Resultado: La diferencia queda almacenada en Z.
 */
void subBlock(const long long* X, std::size_t ldx,
              const long long* Y, std::size_t ldy,
              long long* Z, std::size_t ldz, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = 0; j < n; ++j)
            Z[i * ldz + j] = X[i * ldx + j] - Y[i * ldy + j];
}

/**
 * Función: Producto clásico de bloques, C = A · B (caso base de la recursión).
 * Parámetros:
 * - A, lda: primer bloque y distancia entre sus filas.
 * - B, ldb: segundo bloque y distancia entre sus filas.
 * - C, ldc: bloque de salida y distancia entre sus filas.
 * - n: dimensión de los bloques.
 * Resultado: El producto queda almacenado en C.
 */
void naiveBlock(const long long* A, std::size_t lda,
                const long long* B, std::size_t ldb,
                long long* C, std::size_t ldc, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            long long sum = 0;
            for (std::size_t k = 0; k < n; ++k)
                sum += A[i * lda + k] * B[k * ldb + j];
            C[i * ldc + j] = sum;
        }
    }
}

/**
 * Función: Recursión de Strassen, C = A · B con n potencia de dos.
 * Parámetros:
 * - A, lda: primer bloque y distancia entre sus filas.
 * - B, ldb: segundo bloque y distancia entre sus filas.
 * - C, ldc: bloque de salida y distancia entre sus filas.
 * - n: dimensión de los bloques.
 * Resultado: El producto queda almacenado en C.
 */
void strassenRec(const long long* A, std::size_t lda,
                 const long long* B, std::size_t ldb,
                 long long* C, std::size_t ldc, std::size_t n) {
    if (n <= strassenCutoff || n % 2 != 0) {
        naiveBlock(A, lda, B, ldb, C, ldc, n);
        return;
    }

    const std::size_t h = n / 2;   // dimensión de los bloques
    const std::size_t sz = h * h;

    // Vistas de los cuatro bloques de A y de B (sin copiar).
    const long long* A11 = A;
    const long long* A12 = A + h;
    const long long* A21 = A + h * lda;
    const long long* A22 = A + h * lda + h;

    const long long* B11 = B;
    const long long* B12 = B + h;
    const long long* B21 = B + h * ldb;
    const long long* B22 = B + h * ldb + h;

    // Bloques de salida (sobre el propio C, con su distancia de fila).
    long long* C11 = C;
    long long* C12 = C + h;
    long long* C21 = C + h * ldc;
    long long* C22 = C + h * ldc + h;

    // Una sola reserva para los siete productos y los dos temporales.
    std::vector<long long> work(9 * sz);
    long long* M[7];
    for (int t = 0; t < 7; ++t) M[t] = work.data() + static_cast<std::size_t>(t) * sz;
    long long* T1 = work.data() + 7 * sz;
    long long* T2 = work.data() + 8 * sz;

    // M1 = (A11 + A22) * (B11 + B22)
    addBlock(A11, lda, A22, lda, T1, h, h);
    addBlock(B11, ldb, B22, ldb, T2, h, h);
    strassenRec(T1, h, T2, h, M[0], h, h);

    // M2 = (A21 + A22) * B11
    addBlock(A21, lda, A22, lda, T1, h, h);
    strassenRec(T1, h, B11, ldb, M[1], h, h);

    // M3 = A11 * (B12 - B22)
    subBlock(B12, ldb, B22, ldb, T2, h, h);
    strassenRec(A11, lda, T2, h, M[2], h, h);

    // M4 = A22 * (B21 - B11)
    subBlock(B21, ldb, B11, ldb, T2, h, h);
    strassenRec(A22, lda, T2, h, M[3], h, h);

    // M5 = (A11 + A12) * B22
    addBlock(A11, lda, A12, lda, T1, h, h);
    strassenRec(T1, h, B22, ldb, M[4], h, h);

    // M6 = (A21 - A11) * (B11 + B12)
    subBlock(A21, lda, A11, lda, T1, h, h);
    addBlock(B11, ldb, B12, ldb, T2, h, h);
    strassenRec(T1, h, T2, h, M[5], h, h);

    // M7 = (A12 - A22) * (B21 + B22)
    subBlock(A12, lda, A22, lda, T1, h, h);
    addBlock(B21, ldb, B22, ldb, T2, h, h);
    strassenRec(T1, h, T2, h, M[6], h, h);

    // Recomposición de los cuatro cuadrantes de C.
    for (std::size_t i = 0; i < h; ++i) {
        for (std::size_t j = 0; j < h; ++j) {
            const std::size_t p = i * h + j;
            C11[i * ldc + j] = M[0][p] + M[3][p] - M[4][p] + M[6][p];
            C12[i * ldc + j] = M[2][p] + M[4][p];
            C21[i * ldc + j] = M[1][p] + M[3][p];
            C22[i * ldc + j] = M[0][p] - M[1][p] + M[2][p] + M[5][p];
        }
    }
}

/**
 * Función: Calcula la siguiente potencia de dos mayor o igual que n.
 * Parámetros: n es el valor de referencia.
 * Retorno: Potencia de dos calculada.
 */
std::size_t nextPowerOfTwo(std::size_t n) {
    std::size_t p = 1;
    while (p < n) p <<= 1;
    return p;
}

}  // namespace

// Documentada en matrix.hpp.
Matrix strassenMultiply(const Matrix& A, const Matrix& B) {
    const std::size_t n = A.n;
    if (n == 0) return Matrix(0);

    const std::size_t m = nextPowerOfTwo(n);

    if (m == n) {
        // Tamaños del enunciado: no hace falta rellenar.
        Matrix C(n);
        strassenRec(A.data.data(), n, B.data.data(), n, C.data.data(), n, n);
        return C;
    }

    // Se rellena hasta una potencia de dos porque la recursión divide en
    // mitades; al final se recorta.
    Matrix Ap(m), Bp(m), Cp(m);
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j < n; ++j) {
            Ap(i, j) = A(i, j);
            Bp(i, j) = B(i, j);
        }
    }
    strassenRec(Ap.data.data(), m, Bp.data.data(), m, Cp.data.data(), m, m);

    Matrix C(n);
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = 0; j < n; ++j)
            C(i, j) = Cp(i, j);
    return C;
}
