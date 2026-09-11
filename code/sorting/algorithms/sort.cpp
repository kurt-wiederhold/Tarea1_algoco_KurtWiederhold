/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Archivo entregado con la plantilla de la tarea: la función sortArray es la
 * original del material, sin cambios. Solo se agregó esta documentación.
 * Su firma es la que adoptan las otras tres implementaciones.
 *
 * std::sort en libstdc++, libc++ y MSVC es introsort: quick sort con mediana
 * de tres que cambia a heap sort si la recursión se hace muy profunda y
 * remata los tramos pequeños (≤ 16) con insertion sort. Sirve de línea base.
 * Complejidad: O(n log n) en el peor caso (lo exige el estándar), Θ(log n)
 * de pila y sin memoria auxiliar en el heap. No es estable.
 *
 * Referencias:
 * - Musser, "Introspective Sorting and Selection Algorithms", SP&E 27(8), 1997.
 * - ISO/IEC 14882:2020, [alg.sort]; cppreference, std::sort.
 */

#include <algorithm>
#include <vector>

// Función entregada con el material (ver cabecera). Documentada en algorithms.hpp.
std::vector<int> sortArray(std::vector<int>& arr) {
    std::sort(arr.begin(), arr.end());  // std::sort de la STL
    return arr;
}
