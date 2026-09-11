/**
 * INF-221 Algoritmos y Complejidad
 * Tarea 1, semestre 2026-2
 * Autor: Kurt Wiederhold
 * Rol: 202473528-4
 *
 * Implementación de benchmark.hpp. Para saber cuánto libera cada delete se
 * guarda el tamaño del bloque en una cabecera de kHeader bytes delante de
 * cada asignación y se devuelve al usuario el puntero desplazado.
 *
 * Los operadores alineados de C++17 (align_val_t) no se reemplazan: el
 * compilador siempre empareja new alineado con delete alineado, así que esos
 * bloques nunca pasan por aquí, y ningún tipo usado en la tarea los necesita.
 *
 * Referencias: las mismas de benchmark.hpp.
 */

#include "benchmark.hpp"

#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <new>

#if defined(_WIN32)
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #ifndef NOMINMAX
    #define NOMINMAX
  #endif
  #include <windows.h>
  #include <psapi.h>
#else
  #include <sys/resource.h>
  #include <sys/time.h>
#endif

namespace {

// Cabecera delante de cada bloque; del tamaño de max_align_t para no romper
// la alineación de lo que venga después.
constexpr std::size_t kHeader = alignof(std::max_align_t);

// El programa es de un solo hilo, así que bastan variables simples (sin
// atómicos el sobrecosto queda por debajo del ruido de medición).
std::size_t g_live = 0;      // bytes vivos en total
std::size_t g_baseline = 0;  // bytes vivos al llamar a resetHeapPeak()
std::size_t g_peak = 0;      // máximo de (g_live - g_baseline) observado

inline void noteAllocation(std::size_t bytes) {
    g_live += bytes;
    if (g_live > g_baseline) {
        const std::size_t above = g_live - g_baseline;
        if (above > g_peak) g_peak = above;
    }
}

inline void noteDeallocation(std::size_t bytes) {
    g_live = (g_live >= bytes) ? g_live - bytes : 0;
}

/**
 * Función: Reserva size bytes con malloc y anota el tamaño en la cabecera.
 * Parámetros: size es la cantidad de bytes pedida por el usuario.
 * Retorno: Puntero al área utilizable, o nullptr si malloc falla.
 */
inline void* allocate(std::size_t size) {
    void* raw = std::malloc(size + kHeader);
    if (raw == nullptr) return nullptr;
    std::memcpy(raw, &size, sizeof(std::size_t));
    noteAllocation(size);
    return static_cast<char*>(raw) + kHeader;
}

/**
 * Función: Libera un bloque devuelto por allocate() y descuenta su tamaño.
 * Parámetros: ptr es el puntero que recibió el usuario (puede ser nullptr).
 * Resultado: El bloque queda liberado y g_live actualizado.
 */
inline void deallocate(void* ptr) {
    if (ptr == nullptr) return;
    char* raw = static_cast<char*>(ptr) - kHeader;
    std::size_t size = 0;
    std::memcpy(&size, raw, sizeof(std::size_t));
    noteDeallocation(size);
    std::free(raw);
}

}  // namespace

// Reemplazo de los operadores globales de asignación.

void* operator new(std::size_t size) {
    void* p = allocate(size);
    if (p == nullptr) throw std::bad_alloc();
    return p;
}

void* operator new[](std::size_t size) {
    void* p = allocate(size);
    if (p == nullptr) throw std::bad_alloc();
    return p;
}

void* operator new(std::size_t size, const std::nothrow_t&) noexcept {
    return allocate(size);
}

void* operator new[](std::size_t size, const std::nothrow_t&) noexcept {
    return allocate(size);
}

void operator delete(void* ptr) noexcept                      { deallocate(ptr); }
void operator delete[](void* ptr) noexcept                    { deallocate(ptr); }
void operator delete(void* ptr, std::size_t) noexcept         { deallocate(ptr); }
void operator delete[](void* ptr, std::size_t) noexcept       { deallocate(ptr); }
void operator delete(void* ptr, const std::nothrow_t&) noexcept   { deallocate(ptr); }
void operator delete[](void* ptr, const std::nothrow_t&) noexcept { deallocate(ptr); }

namespace bench {

void resetHeapPeak() {
    g_baseline = g_live;
    g_peak = 0;
}

std::size_t peakHeapBytes() { return g_peak; }

std::size_t currentHeapBytes() {
    return (g_live > g_baseline) ? (g_live - g_baseline) : 0;
}

std::size_t peakResidentBytes() {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS pmc;
    std::memset(&pmc, 0, sizeof(pmc));
    pmc.cb = sizeof(pmc);
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) {
        return static_cast<std::size_t>(pmc.PeakWorkingSetSize);
    }
    return 0;
#else
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
  #if defined(__APPLE__)
        return static_cast<std::size_t>(usage.ru_maxrss);          // bytes
  #else
        return static_cast<std::size_t>(usage.ru_maxrss) * 1024u;  // KiB -> bytes
  #endif
    }
    return 0;
#endif
}

}  // namespace bench
