/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Declaraciones de los cuatro algoritmos de ordenamiento del experimento.
 * Todos usan la firma del sort.cpp entregado con el material,
 * std::vector<int> f(std::vector<int>& arr): ordenan el arreglo en el lugar
 * y devuelven una copia. Así el programa principal los invoca de forma
 * uniforme con un puntero a función y los mide exactamente igual.
 *
 * Esa copia de retorno (4n bytes, Θ(n) de tiempo) queda dentro de la región
 * medida en los cuatro casos; el informe la tiene en cuenta.
 *
 * Referencias generales:
 * - Cormen et al., Introduction to Algorithms, 3.ª ed., caps. 2, 6 y 7.
 * - Knuth, TAOCP vol. 3, 2.ª ed.
 * Las referencias específicas de cada algoritmo van en su archivo.
 */

#ifndef SORTING_ALGORITHMS_HPP
#define SORTING_ALGORITHMS_HPP

#include <vector>

/**
 * Función: Ordena con std::sort (implementación entregada en el material).
 * Parámetros: arr es el arreglo que se ordenará en el lugar.
 * Retorno: Copia ordenada del arreglo.
 * Complejidad: O(n log n) en tiempo; sin memoria auxiliar en el heap.
 */
std::vector<int> sortArray(std::vector<int>& arr);

/**
 * Función: Ordena el arreglo mediante Merge Sort (top-down).
 * Parámetros: arr es el arreglo que se ordenará en el lugar.
 * Retorno: Copia ordenada del arreglo.
 * Complejidad: Θ(n log n) en tiempo y Θ(n) de memoria auxiliar.
 */
std::vector<int> mergeSort(std::vector<int>& arr);

/**
 * Función: Ordena el arreglo mediante Quick Sort (partición de Hoare,
 * pivote mediana de tres).
 * Parámetros: arr es el arreglo que se ordenará en el lugar.
 * Retorno: Copia ordenada del arreglo.
 * Complejidad: Θ(n log n) en promedio, Θ(n²) en el peor caso; Θ(log n) de pila.
 */
std::vector<int> quickSort(std::vector<int>& arr);

/**
 * Función: Ordena el arreglo mediante Patience Sort (pilas + mezcla k-vías).
 * Parámetros: arr es el arreglo que se ordenará en el lugar.
 * Retorno: Copia ordenada del arreglo.
 * Complejidad: Θ(n log k) con k pilas (Θ(n) si la entrada es descendente,
 * O(n log n) en el peor caso); Θ(n) de memoria auxiliar.
 */
std::vector<int> patienceSort(std::vector<int>& arr);

#endif  // SORTING_ALGORITHMS_HPP
