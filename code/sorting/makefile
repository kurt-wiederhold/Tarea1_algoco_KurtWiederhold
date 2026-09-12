# =============================================================================
#  INF-221 Algoritmos y Complejidad -- Semestre 2026-2
#  Tarea 1: «Más allá de la notación asintótica»
#  Autor: Kurt Wiederhold        Rol: 202473528-4
#
#  Archivo: code/sorting/makefile
#
#  Compila y ejecuta el experimento de ORDENAMIENTO.
#
#  Objetivos principales:
#     make            compila el binario ./sorting
#     make data       genera los casos de prueba en data/array_input/
#     make run        ejecuta las mediciones -> data/measurements/*.csv
#     make plots      genera los graficos    -> data/plots/*.png
#     make experiment data + run + plots (experimento completo)
#     make clean      borra el binario
#     make help       lista todos los objetivos
#
#  Notas sobre las banderas de compilacion:
#   -std=c++17  se usa std::filesystem para recorrer los directorios de datos.
#   -O2         nivel de optimizacion estandar. Se evita -O3 y -march=native a
#               proposito: -march=native ata los resultados al procesador
#               exacto de esta maquina y haria irreproducible el experimento en
#               otro equipo, que es justo lo contrario de lo que se busca.
#   -Wall -Wextra  con g++ 16.1.0 no hay advertencias; otras versiones de GCC
#               pueden emitir -Warray-bounds (falso positivo al copiar el
#               std::vector de retorno) sin afectar la compilacion.
#
#  Este makefile es GNU make estandar. En Windows se probo con mingw32-make de
#  MinGW-w64 (ver code/README.md).
# =============================================================================

CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
PYTHON   ?= python

# --- Diferencias entre sistemas operativos ----------------------------------
# En Windows se necesita -lpsapi para GetProcessMemoryInfo (memoria residente).
ifeq ($(OS),Windows_NT)
  EXE      := .exe
  LDLIBS   := -lpsapi
  # Enlace estatico de las bibliotecas de GCC: el ejecutable resultante no
  # depende de libstdc++-6.dll ni de libgcc_s_seh-1.dll, asi que puede ejecutarse
  # sin tener el directorio bin de MinGW en el PATH.
  LDFLAGS  := -static -static-libgcc -static-libstdc++
  # `del` es un builtin de cmd.exe, no un ejecutable: GNU make no puede
  # invocarlo directamente con CreateProcess, hay que pasar por `cmd /c`.
  RM_F     := cmd /c del /Q /F
  FIXPATH   = $(subst /,\,$1)
else
  EXE      :=
  LDLIBS   :=
  LDFLAGS  :=
  RM_F     := rm -f
  FIXPATH   = $1
endif

TARGET := sorting$(EXE)

# Como se invoca el binario recien construido: en POSIX hace falta el "./",
# mientras que cmd.exe de Windows no entiende esa forma.
ifeq ($(OS),Windows_NT)
  RUNCMD := $(TARGET)
else
  RUNCMD := ./$(TARGET)
endif

SRCS := sorting.cpp \
        algorithms/sort.cpp \
        algorithms/mergesort.cpp \
        algorithms/quicksort.cpp \
        algorithms/patiencesort.cpp \
        ../common/benchmark.cpp

HDRS := algorithms/algorithms.hpp ../common/benchmark.hpp

# Argumentos que se pasan al binario en `make run` (sobrescribibles desde la
# linea de comandos, p. ej.:  make run RUN_ARGS="--max-n 100000")
RUN_ARGS ?=

.PHONY: all data run plots experiment clean help

all: $(TARGET)

$(TARGET): $(SRCS) $(HDRS)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS) $(LDLIBS)

# Los generadores entregados con el material escriben en la ruta relativa
# ../data/..., por lo que deben ejecutarse desde el directorio scripts/.
data:
	cd scripts && $(PYTHON) array_generator.py

run: $(TARGET)
	$(RUNCMD) $(RUN_ARGS)

plots:
	$(PYTHON) scripts/plot_generator.py

experiment: data run plots

clean:
	-$(RM_F) $(call FIXPATH,$(TARGET))


help:
	@echo "Objetivos disponibles:"
	@echo "  make            compila ./$(TARGET)"
	@echo "  make data       genera los arreglos de prueba en data/array_input/"
	@echo "  make run        ejecuta las mediciones (usa RUN_ARGS para opciones)"
	@echo "  make plots      genera los graficos en data/plots/"
	@echo "  make experiment data + run + plots"
	@echo "  make clean      borra el binario"
	@echo ""
	@echo "Ejemplos:"
	@echo "  make experiment"
	@echo "  make run RUN_ARGS=\"--max-n 100000 --reps 5\""
