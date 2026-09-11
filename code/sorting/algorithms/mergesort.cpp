/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Merge sort recursivo (top-down) para el análisis experimental.
 * Complejidad: Θ(n log n) en tiempo en todos los casos, Θ(n) de memoria
 * auxiliar (un solo búfer) y Θ(log n) de pila. Es estable.
 *
 * Referencias:
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., sección 2.3.1.
 * - Sedgewick y Wayne, Algorithms, 4.ª ed., sección 2.2 (búfer único).
 *
 * Implementación propia a partir del pseudocódigo clásico.
 */

#include "algorithms.hpp"

#include <cstddef>
#include <vector>

namespace {

/**
 * Función: Mezcla los tramos ordenados [lo, mid) y [mid, hi).
 * Parámetros:
 * - a: arreglo que contiene ambos tramos.
 * - buf: búfer auxiliar del mismo tamaño que a.
 * - lo: inicio del primer tramo.
 * - mid: fin del primero e inicio del segundo.
 * - hi: fin del segundo tramo.
 * Resultado: [lo, hi) queda ordenado en a.
 */
void merge(std::vector<int>& a, std::vector<int>& buf,
           std::size_t lo, std::size_t mid, std::size_t hi) {
    std::size_t i = lo;   // cursor sobre la mitad izquierda
    std::size_t j = mid;  // cursor sobre la mitad derecha
    std::size_t k = lo;   // cursor de escritura sobre el buffer

    while (i < mid && j < hi) {
        // `<=` toma primero el de la izquierda en caso de empate (estabilidad).
        buf[k++] = (a[i] <= a[j]) ? a[i++] : a[j++];
    }
    while (i < mid) buf[k++] = a[i++];
    while (j < hi)  buf[k++] = a[j++];

    for (std::size_t t = lo; t < hi; ++t) a[t] = buf[t];
}

/**
 * Función: Ordena recursivamente el tramo [lo, hi).
 * Parámetros:
 * - a: arreglo a ordenar.
 * - buf: búfer auxiliar compartido por toda la recursión.
 * - lo: inicio del tramo.
 * - hi: fin del tramo (exclusivo).
 * Resultado: [lo, hi) queda ordenado en a.
 */
void mergeSortRec(std::vector<int>& a, std::vector<int>& buf,
                  std::size_t lo, std::size_t hi) {
    if (hi - lo < 2) return;                 // 0 ó 1 elemento: ya está ordenado
    const std::size_t mid = lo + (hi - lo) / 2;  // evita desbordamiento
    mergeSortRec(a, buf, lo, mid);
    mergeSortRec(a, buf, mid, hi);
    // A propósito no se salta la mezcla cuando a[mid-1] <= a[mid]: así el
    // algoritmo hace el mismo trabajo con cualquier entrada, que es lo que se
    // quiere contrastar con quick sort y patience sort.
    merge(a, buf, lo, mid, hi);
}

}  // namespace

// Documentada en algorithms.hpp.
std::vector<int> mergeSort(std::vector<int>& arr) {
    if (arr.size() < 2) return arr;
    std::vector<int> buf(arr.size());        // único buffer auxiliar: Θ(n)
    mergeSortRec(arr, buf, 0, arr.size());
    return arr;
}
