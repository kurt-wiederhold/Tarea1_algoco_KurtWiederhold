/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Quick sort con partición de Hoare y pivote mediana de tres.
 * Complejidad: Θ(n log n) en promedio, Θ(n²) en el peor caso; Θ(1) de
 * memoria auxiliar y Θ(log n) de pila (se recurre sobre el lado menor).
 * No es estable.
 *
 * Dos decisiones importan para los casos del enunciado: la mediana de tres
 * evita el peor caso con entradas ya ordenadas, y la partición de Hoare
 * reparte los repetidos entre ambos lados, así que el dominio D1 (solo diez
 * valores distintos) no degenera a Θ(n²) como pasaría con Lomuto.
 *
 * Referencias:
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., cap. 7 y problema 7-1.
 * - Hoare, "Quicksort", The Computer Journal 5(1), 1962.
 * - Sedgewick, "Implementing Quicksort Programs", CACM 21(10), 1978.
 *
 * Implementación propia a partir del pseudocódigo de las referencias.
 */

#include "algorithms.hpp"

#include <cstddef>
#include <utility>
#include <vector>

namespace {

/**
 * Función: Ordena entre sí a[lo], a[mid] y a[hi] y ubica la mediana.
 * Parámetros:
 * - a: arreglo.
 * - lo: primer índice del tramo.
 * - hi: último índice del tramo (inclusive).
 * Retorno: Índice de la mediana (el central); queda a[lo] <= a[mid] <= a[hi].
 */
std::size_t medianOfThree(std::vector<int>& a, std::size_t lo, std::size_t hi) {
    const std::size_t mid = lo + (hi - lo) / 2;
    if (a[mid] < a[lo])  std::swap(a[mid], a[lo]);
    if (a[hi]  < a[lo])  std::swap(a[hi],  a[lo]);
    if (a[hi]  < a[mid]) std::swap(a[hi],  a[mid]);
    return mid;  // a[lo] <= a[mid] <= a[hi]
}

/**
 * Función: Partición de Hoare sobre el tramo cerrado [lo, hi].
 * Parámetros:
 * - a: arreglo.
 * - lo: primer índice del tramo.
 * - hi: último índice del tramo.
 * Retorno: Índice j con lo <= j < hi tal que todo [lo, j] es <= pivote y
 * todo [j+1, hi] es >= pivote.
 */
std::size_t hoarePartition(std::vector<int>& a, std::size_t lo, std::size_t hi) {
    // La mediana se lleva a a[lo] para quedar en el esquema de Hoare que
    // analiza CLRS (problema 7-1), cuya demostración garantiza lo <= j < hi.
    std::swap(a[lo], a[medianOfThree(a, lo, hi)]);
    const int pivot = a[lo];

    // lo-1 y hi+1 se calculan en aritmética modular de size_t; el primer
    // incremento/decremento los devuelve al rango válido.
    std::size_t i = lo - 1;
    std::size_t j = hi + 1;

    while (true) {
        // a[lo] == pivot hace de centinela por ambos lados: ningún bucle se
        // sale del tramo.
        do { ++i; } while (a[i] < pivot);
        do { --j; } while (a[j] > pivot);
        if (i >= j) return j;
        std::swap(a[i], a[j]);
    }
}

/**
 * Función: Ordena el tramo cerrado [lo, hi] de forma recursiva.
 * Parámetros:
 * - a: arreglo.
 * - lo: primer índice del tramo.
 * - hi: último índice del tramo.
 * Resultado: [lo, hi] queda ordenado en a.
 */
void quickSortRec(std::vector<int>& a, std::size_t lo, std::size_t hi) {
    while (lo < hi) {
        const std::size_t p = hoarePartition(a, lo, hi);
        // Se recurre sobre el lado menor y se itera sobre el mayor para que la
        // profundidad de la pila sea O(log n) incluso en el peor caso.
        if (p - lo < hi - (p + 1)) {
            quickSortRec(a, lo, p);
            lo = p + 1;
        } else {
            quickSortRec(a, p + 1, hi);
            hi = p;
        }
    }
}

}  // namespace

// Documentada en algorithms.hpp.
std::vector<int> quickSort(std::vector<int>& arr) {
    if (arr.size() < 2) return arr;
    quickSortRec(arr, 0, arr.size() - 1);
    return arr;
}
