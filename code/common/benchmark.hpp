/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Utilidades de medición compartidas por los dos programas principales
 * (sorting.cpp y matrix_multiplication.cpp): un cronómetro monótono y un
 * contador de memoria dinámica basado en reemplazar los operadores globales
 * new/delete. Se comparte para que ambos experimentos midan igual.
 *
 * El contador de heap cuenta bytes vivos desde el último resetHeapPeak(); no
 * incluye la pila de llamadas ni memoria pedida con malloc directo.
 *
 * Referencias:
 * - ISO/IEC 14882:2020, [new.delete] y [time.clock.steady].
 * - cppreference, "operator new / operator delete" (formas reemplazables).
 * - Microsoft Learn, GetProcessMemoryInfo (psapi.h); man getrusage(2).
 *
 * Implementación propia.
 */

#ifndef BENCHMARK_HPP
#define BENCHMARK_HPP

#include <chrono>
#include <cstddef>

namespace bench {

/**
 * Cronómetro sobre steady_clock. Se usa este reloj y no system_clock porque
 * es monótono: un ajuste de hora del sistema no puede producir tiempos
 * negativos en una medición larga.
 */
class Timer {
public:
    Timer() : start_(std::chrono::steady_clock::now()) {}

    void reset() { start_ = std::chrono::steady_clock::now(); }

    /**
     * Función: Tiempo transcurrido desde la construcción o el último reset().
     * Retorno: Milisegundos, con parte decimal.
     */
    double elapsedMs() const {
        const auto end = std::chrono::steady_clock::now();
        return std::chrono::duration<double, std::milli>(end - start_).count();
    }

private:
    std::chrono::steady_clock::time_point start_;
};

/**
 * Función: Reinicia el contador de pico y toma como línea base los bytes
 * vivos en este instante. Hay que llamarla justo antes de la región a medir.
 * Resultado: peakHeapBytes() vuelve a partir de cero.
 */
void resetHeapPeak();

/**
 * Función: Pico de memoria dinámica desde el último resetHeapPeak().
 * Retorno: Máximo de bytes vivos por encima de la línea base.
 */
std::size_t peakHeapBytes();

/**
 * Función: Memoria dinámica viva en este momento.
 * Retorno: Bytes vivos por encima de la línea base.
 */
std::size_t currentHeapBytes();

/**
 * Función: Pico de memoria residente del proceso completo (working set en
 * Windows, ru_maxrss en POSIX). Sirve de contraste con el contador de heap.
 * Retorno: Bytes, o 0 si el sistema no lo informa.
 */
std::size_t peakResidentBytes();

}  // namespace bench

#endif  // BENCHMARK_HPP
