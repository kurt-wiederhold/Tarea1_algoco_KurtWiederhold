/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Patience sort: se reparten los elementos en pilas como en el solitario del
 * mismo nombre (cada uno va a la pila más a la izquierda cuya cima sea >= él,
 * o abre una nueva) y luego se mezclan las k pilas con un min-heap.
 * Complejidad: Θ(n log k) en tiempo, con k el número de pilas; Θ(n) si la
 * entrada es descendente (una sola pila) y O(n log n) en el peor caso.
 * Θ(n) de memoria auxiliar. No es estable.
 *
 * Las pilas se representan con punteros hacia abajo en dos arreglos planos en
 * vez de vector<vector<int>>: con n = 10^7 ascendente hay millones de pilas y
 * un vector por pila costaría cientos de MB solo en cabeceras. Con valores
 * repetidos k es el número de valores distintos, no n, porque un elemento
 * igual a la cima se apila sobre ella.
 *
 * Referencias:
 * - Mallows, "Patience sorting", SIAM Review 5(4), 1963.
 * - Aldous y Diaconis, "Longest increasing subsequences: from patience
 *   sorting to the Baik-Deift-Johansson theorem", Bull. AMS 36(4), 1999
 *   (descripción del solitario y punteros hacia atrás).
 * - Chandramouli y Goldstein, "Patience is a Virtue", SIGMOD 2014 (mezcla
 *   k-vías de las pilas).
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., cap. 6 (heaps).
 *
 * Implementación propia a partir de la descripción de las referencias.
 */

#include "algorithms.hpp"

#include <algorithm>
#include <cstddef>
#include <queue>
#include <utility>
#include <vector>

namespace {

/**
 * Elemento del heap de la mezcla: el valor y su índice en arr. El operador <
 * está invertido porque priority_queue es un max-heap y aquí se necesita
 * extraer el mínimo.
 */
struct HeapItem {
    int value;
    int index;
    bool operator<(const HeapItem& other) const { return value > other.value; }
};

}  // namespace

// Documentada en algorithms.hpp.
std::vector<int> patienceSort(std::vector<int>& arr) {
    const std::size_t n = arr.size();
    if (n < 2) return arr;

    // Fase 1: repartir en pilas.
    std::vector<int> below(n, -1);  // below[i]: elemento bajo i en su pila
    std::vector<int> topIdx;        // topIdx[p]: cima de la pila p
    topIdx.reserve(64);

    for (std::size_t i = 0; i < n; ++i) {
        const int v = arr[i];

        // Las cimas quedan siempre en orden no decreciente, así que la pila
        // destino se encuentra con búsqueda binaria.
        std::size_t lo = 0, hi = topIdx.size();
        while (lo < hi) {
            const std::size_t mid = lo + (hi - lo) / 2;
            if (arr[topIdx[mid]] >= v) hi = mid;
            else                       lo = mid + 1;
        }

        if (lo == topIdx.size()) {
            topIdx.push_back(static_cast<int>(i));   // se abre una pila nueva
        } else {
            below[i] = topIdx[lo];                   // v se apila sobre esa cima
            topIdx[lo] = static_cast<int>(i);
        }
    }

    // Fase 2: cada pila leída desde la cima es no decreciente, así que basta
    // un min-heap con las k cimas e ir reemplazando cada extraído por el
    // elemento que tenía debajo.
    std::vector<HeapItem> seeds;
    seeds.reserve(topIdx.size());
    for (const int t : topIdx) seeds.push_back(HeapItem{arr[t], t});

    std::priority_queue<HeapItem> heap(std::less<HeapItem>(), std::move(seeds));

    std::vector<int> result;
    result.reserve(n);
    while (!heap.empty()) {
        const HeapItem item = heap.top();
        heap.pop();
        result.push_back(item.value);
        const int next = below[item.index];
        if (next >= 0) heap.push(HeapItem{arr[next], next});
    }

    arr = std::move(result);
    return arr;
}
