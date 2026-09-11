# =============================================================================
#  INF-221 Algoritmos y Complejidad -- Semestre 2026-2
#  Tarea 1: «Más allá de la notación asintótica»
#  Autor: Kurt Wiederhold        Rol: 202473528-4
#
#  Archivo: code/matrix_multiplication/makefile
#
#  Compila y ejecuta el experimento de MULTIPLICACION DE MATRICES.
#
#  Objetivos principales:
#     make            compila el binario ./matrix_multiplication
#     make data       genera los casos de prueba en data/matrix_input/
#     make run        ejecuta las mediciones -> data/measurements/*.csv
#     make plots      genera los graficos    -> data/plots/*.png
#     make experiment data + run + plots (experimento completo)
#     make cutoff     barrido del umbral de corte de Strassen
#     make type-check control: tipo de matriz vs orden de ejecucion
#     make stride-check control: potencia de dos vs tamanos vecinos (cache)
#     make clean      borra el binario
#     make help       lista todos los objetivos
#
#  Notas sobre las banderas de compilacion: identicas a las del experimento de
#  ordenamiento (ver code/sorting/makefile). En particular se evita
#  -march=native para que las mediciones sean reproducibles en otra maquina.
# =============================================================================

CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
PYTHON   ?= python

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

TARGET := matrix_multiplication$(EXE)

# Como se invoca el binario recien construido: en POSIX hace falta el "./",
# mientras que cmd.exe de Windows no entiende esa forma.
ifeq ($(OS),Windows_NT)
  RUNCMD := $(TARGET)
else
  RUNCMD := ./$(TARGET)
endif

SRCS := matrix_multiplication.cpp \
        algorithms/naive.cpp \
        algorithms/strassen.cpp \
        ../common/benchmark.cpp

HDRS := algorithms/matrix.hpp ../common/benchmark.hpp

RUN_ARGS ?=

# Umbrales del barrido de `make cutoff` (decision de diseno (a) de strassen.cpp).
CUTOFFS ?= 1 2 4 8 16 32 64 128 256

.PHONY: all data run plots experiment cutoff type-check stride-check clean help

all: $(TARGET)

$(TARGET): $(SRCS) $(HDRS)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET) $(LDFLAGS) $(LDLIBS)

# Los generadores entregados con el material escriben en la ruta relativa
# ../data/..., por lo que deben ejecutarse desde el directorio scripts/.
data:
	cd scripts && $(PYTHON) matrix_generator.py

run: $(TARGET)
	$(RUNCMD) $(RUN_ARGS)

plots:
	$(PYTHON) scripts/plot_generator.py

experiment: data run plots

# Barrido del umbral de corte de Strassen: mide el mismo conjunto de casos
# variando el tamano al que la recursion delega en el algoritmo clasico.
# El barrido se orquesta desde Python y no desde el shell del makefile para
# que el objetivo funcione igual en POSIX y en cmd.exe de Windows.
cutoff: $(TARGET)
	$(PYTHON) scripts/cutoff_sweep.py --cutoffs $(CUTOFFS)

# Experimento de control: mide cada tipo de matriz en un proceso independiente y
# siempre en primera posicion, para separar el efecto del tipo del efecto del
# orden de ejecucion (calentamiento del procesador). Respalda el ultimo parrafo
# de la seccion de resultados del informe.
type-check: $(TARGET)
	$(PYTHON) scripts/type_order_check.py

# Experimento de control: mide el metodo clasico en n = 1024 y en tamanos
# vecinos (1000, 1040, ...) que ocupan la misma memoria pero cuyo stride no es
# potencia de dos. Separa el efecto de la CAPACIDAD de la cache del efecto de
# los CONFLICTOS de conjunto. Respalda el parrafo sobre los exponentes medidos.
stride-check: $(TARGET)
	$(PYTHON) scripts/stride_check.py

clean:
	-$(RM_F) $(call FIXPATH,$(TARGET))


help:
	@echo "Objetivos disponibles:"
	@echo "  make            compila ./$(TARGET)"
	@echo "  make data       genera las matrices de prueba en data/matrix_input/"
	@echo "  make run        ejecuta las mediciones (usa RUN_ARGS para opciones)"
	@echo "  make plots      genera los graficos en data/plots/"
	@echo "  make experiment data + run + plots"
	@echo "  make cutoff     barrido del umbral de corte de Strassen"
	@echo "  make type-check control: tipo de matriz vs orden de ejecucion"
	@echo "  make stride-check control: potencia de dos vs tamanos vecinos"
	@echo "  make clean      borra el binario"
	@echo ""
	@echo "Ejemplos:"
	@echo "  make experiment"
	@echo "  make run RUN_ARGS=\"--max-n 256 --cutoff 32\""
