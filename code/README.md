# Documentación — Tarea 1 INF-221 Algoritmos y Complejidad

**Autor:** Kurt Wiederhold — **Rol:** 202473528-4
**Ramo:** INF-221 Algoritmos y Complejidad — **Semestre:** 2026-2
**Tarea:** 1 — *«Más allá de la notación asintótica: análisis experimental de
algoritmos de ordenamiento y multiplicación de matrices»*

## Entrega

La entrega se realiza vía **aula.usm.cl** en formato `.zip`.

> **Nota sobre el límite de la entrega.** El archivo enviado a Aula no puede
> superar los 50 MB. Por esta razón, se omiten únicamente los 18 archivos de
> entrada y los 18 archivos de salida de ordenamiento correspondientes a
> `n = 10^7`, que ocupan aproximadamente 1,7 GB sin comprimir. La entrega
> contiene 54 de los 72 archivos de `data/array_input/` y 54 de los 72 de
> `data/array_output/` (todos los casos con n ≤ 10^5); las matrices están
> completas (144 entradas y 72 salidas).
>
> La entrega conserva el generador de casos, el programa que ejecuta los cuatro
> algoritmos, las mediciones completas de `n = 10^7` (las 2 880 filas del CSV
> de ordenamiento, incluidas las 18 familias con n = 10^7, todas con
> `correct = 1`), los gráficos, las tablas, las macros y el informe elaborado
> a partir de esas mediciones. Los archivos omitidos pueden regenerarse
> ejecutando:
>
> ```bash
> cd code/sorting
> make data
> make run
> ```
>
> El generador original no fija una semilla aleatoria. Por ello, una nueva
> ejecución produce casos diferentes de la misma distribución (no una copia
> exacta de los originales). Las mediciones incluidas corresponden a la
> ejecución original utilizada para elaborar el informe y no deben
> reemplazarse ni mezclarse con datos regenerados.

---

## 1. Requisitos

| Herramienta | Versión usada | Para qué |
|---|---|---|
| Compilador C++ | `g++` 16.1.0 (MinGW-w64, UCRT) | programas de medición |
| Estándar | C++17 | `std::filesystem` para recorrer los datos |
| GNU make | `mingw32-make` 4.4.1 | automatización |
| Python | 3.12.10 | generación de datos y de gráficos |
| NumPy | 2.5.2 | generación de los casos de prueba |
| Matplotlib | 3.11.1 | gráficos |

Instalación de las dependencias de Python:

```bash
python -m pip install numpy matplotlib
```

> El código compila correctamente con `-std=c++17 -O2 -Wall -Wextra` (sin
> advertencias con g++ 16.1.0). Dependiendo de la versión de GCC, pueden
> aparecer advertencias `-Warray-bounds` relacionadas con la optimización
> interna de `std::vector` (falso positivo conocido de GCC 12–13 al copiar el
> vector de retorno), sin impedir la compilación ni afectar las pruebas de
> corrección.
>
> En Windows el enlazado es estático (`-static -static-libgcc -static-libstdc++`)
> para que los ejecutables no dependan de las DLL de MinGW, y se enlaza
> `-lpsapi` porque la medición de memoria residente usa `GetProcessMemoryInfo`.
> En Linux y macOS ambas cosas son innecesarias y el `makefile` las omite solo.

---

## 2. Cómo reproducir el experimento completo

Cada uno de los dos experimentos es independiente y se ejecuta de la misma forma:

```bash
cd code/sorting              # o  cd code/matrix_multiplication
make experiment              # = make data + make run + make plots
```

Eso hace tres cosas, en orden:

1. **`make data`** — genera los casos de prueba del anexo A del enunciado en
   `data/array_input/` (72 archivos, ~858 MB) o `data/matrix_input/`
   (144 archivos, ~78 MB).
2. **`make run`** — compila si hace falta, ejecuta todos los algoritmos sobre
   todos los casos y escribe las mediciones crudas en
   `data/measurements/*.csv` y los resultados en `data/array_output/` o
   `data/matrix_output/`.
3. **`make plots`** — lee esos CSV y genera los PNG de `data/plots/`, las
   tablas LaTeX `data/measurements/table_*.tex` **y** el archivo de macros
   `data/measurements/numbers_*.tex` con cada cifra que la prosa del informe
   cita (razones, factores, tiempos puntuales) como un `\newcommand`. Así el
   informe no contiene ningún número escrito a mano y no queda desincronizado
   si se repite el experimento.

Objetivos adicionales:

| Objetivo | Qué hace |
|---|---|
| `make` | solo compila el binario |
| `make cutoff` | (matrices) barrido del umbral de corte de Strassen |
| `make type-check` | (matrices) control: tipo de matriz vs orden de ejecución |
| `make stride-check` | (matrices) control: potencia de dos vs tamaños vecinos (caché) |
| `make clean` | borra el binario |
| `make help` | lista todos los objetivos |

Los binarios aceptan opciones para acortar el experimento; se pasan con
`RUN_ARGS`:

```bash
make run RUN_ARGS="--max-n 100000 --reps 5"     # ordenamiento sin n = 10^7
make run RUN_ARGS="--max-n 256 --cutoff 32"     # matrices hasta 256x256
```

Use `./sorting --help` o `./matrix_multiplication --help` para la lista completa.

---

## 3. Estructura

```
code/
├── common/                              utilidades compartidas por ambos experimentos
│   ├── benchmark.hpp                    interfaz de medición de tiempo y memoria
│   └── benchmark.cpp                    implementación (operadores new/delete instrumentados)
│
├── sorting/
│   ├── makefile
│   ├── sorting.cpp                      programa principal de medición
│   ├── algorithms/
│   │   ├── algorithms.hpp               declaraciones comunes
│   │   ├── sort.cpp                     std::sort (entregado con el material)
│   │   ├── mergesort.cpp                merge sort
│   │   ├── quicksort.cpp                quick sort
│   │   └── patiencesort.cpp             patience sort
│   ├── scripts/
│   │   ├── array_generator.py           genera data/array_input/
│   │   └── plot_generator.py            genera data/plots/, tablas y macros .tex
│   └── data/
│       ├── array_input/                 {n}_{t}_{d}_{m}.txt
│       ├── array_output/                {n}_{t}_{d}_{m}_out.txt
│       ├── measurements/                sorting_measurements.csv + tablas y macros .tex
│       └── plots/                       figuras .png
│
└── matrix_multiplication/
    ├── makefile
    ├── matrix_multiplication.cpp        programa principal de medición
    ├── algorithms/
    │   ├── matrix.hpp                   tipo Matrix y declaraciones
    │   ├── naive.cpp                    multiplicación clásica
    │   └── strassen.cpp                 algoritmo de Strassen
    ├── scripts/
    │   ├── matrix_generator.py          genera data/matrix_input/
    │   ├── cutoff_sweep.py              barrido del umbral de Strassen
    │   ├── type_order_check.py          control: tipo de matriz vs orden de ejecucion
    │   ├── stride_check.py              control: n potencia de dos vs vecinos (cache)
    │   └── plot_generator.py            genera data/plots/, tablas y macros .tex
    └── data/
        ├── matrix_input/                {n}_{t}_{d}_{m}_1.txt y _2.txt
        ├── matrix_output/               {n}_{t}_{d}_{m}_out.txt
        ├── measurements/                *_measurements.csv + tablas y macros .tex
        └── plots/                       figuras .png
```

`common/` no está en la estructura mínima del enunciado; se agregó para que los
dos programas principales midan tiempo y memoria **exactamente de la misma
manera**, en lugar de duplicar el código y arriesgar que diverjan. Todos los
archivos que el enunciado exige están en su ruta original.

---

## 4. Multiplicación de matrices

### 4.1. Algoritmos

| Archivo | Algoritmo | Tiempo | Memoria auxiliar |
|---|---|---|---|
| `algorithms/naive.cpp` | Clásico, tres bucles `i-j-k` | Θ(n³) | Θ(1) |
| `algorithms/strassen.cpp` | Strassen (1969), 7 multiplicaciones por nivel | Θ(n^log₂7) = Θ(n^2,807) | Θ(n²) |

Ambos son **insensibles a los datos**: hacen el mismo trabajo con una matriz
densa, dispersa o diagonal, porque ninguno inspecciona los coeficientes.

> **Advertencia experimental.** El orden de bucles `i-j-k` recorre `B` por
> columnas con un salto de `8n` bytes. Con los tamaños del enunciado (todos
> potencias de dos) ese salto está alineado a página y todos los elementos de
> una columna compiten por el mismo conjunto de la caché, lo que multiplica el
> costo por operación hasta 6× frente a un `n` vecino (véase
> `make stride-check`). Se conserva a propósito la versión «de libro» porque el
> objeto del experimento es medir ese tipo de efectos, no evitarlos; el informe
> los discute.

Decisiones de implementación, documentadas en detalle en la cabecera de cada
archivo fuente:

- **Almacenamiento plano** (`std::vector<long long>` de n·n, orden por filas) en
  vez de `vector<vector<...>>`, para no arruinar la localidad de caché con una
  indirección por acceso.
- **`long long`** como tipo de coeficiente: el producto está acotado por
  9·9·1024 = 82 944, así que `int` bastaría, pero `long long` elimina cualquier
  riesgo de desbordamiento sin cambiar la complejidad.
- **Umbral de corte de Strassen = 64** (opción `--cutoff`). Bajar la recursión
  hasta bloques 1×1 hace que las 18 sumas de bloques y las asignaciones de
  memoria por nivel dominen el ahorro de multiplicaciones. `make cutoff` mide el
  efecto del umbral en lugar de suponerlo.
- **Vistas con *stride*** en la recursión: los bloques no se copian, se pasan
  como puntero más distancia entre filas.
- **Relleno a potencia de dos** si n no lo es. Con los tamaños del enunciado
  (2⁴, 2⁶, 2⁸, 2¹⁰) nunca se activa.

### 4.2. Programa principal — `matrix_multiplication.cpp`

Recorre `data/matrix_input/`, empareja `{base}_1.txt` con `{base}_2.txt`,
ejecuta ambos algoritmos, **verifica** que Strassen coincida coeficiente a
coeficiente con el método clásico, escribe el producto en
`data/matrix_output/{base}_out.txt` y agrega una fila por medición al CSV.

### 4.3. Scripts

- **`scripts/matrix_generator.py`** — genera los pares de matrices del anexo A.2.
- **`scripts/cutoff_sweep.py`** — ejecuta el programa una vez por umbral de
  corte y acumula todo en `strassen_cutoff_sweep.csv` (`make cutoff`).
- **`scripts/type_order_check.py`** — experimento de control (`make type-check`):
  mide cada tipo de matriz en un **proceso independiente y siempre en primera
  posición**, para separar el efecto del tipo de matriz del efecto del orden de
  ejecución (una corrida larga calienta el procesador y baja su frecuencia de
  *boost*, lo que puede hacer parecer más lentos los casos que se procesan al
  final). En las mediciones entregadas la dispersión **relativa** entre tipos
  coincide en ambas formas de medir (6 % en la corrida principal, 6 % con cada
  tipo aislado), confirmando que la estructura de la matriz no influye. El
  nivel **absoluto**, en cambio, no coincide: los tiempos aislados son un 25 %
  más altos que los mismos casos de la corrida principal. Eso no cambia la
  conclusión (afecta por igual a los tres tipos) pero muestra que el nivel
  absoluto de una medición de ~3 s depende del estado de la máquina en ese
  momento; el informe lo declara y por eso sólo compara mediciones de una misma
  corrida. Resultado en `data/measurements/matrix_type_order_check.csv`.
- **`scripts/stride_check.py`** — experimento de control (`make stride-check`):
  mide el método clásico en n = 2^k **y en dimensiones vecinas** (250/256/260,
  500/512/520, 1000/1024/1040) que ocupan la misma memoria pero cuyo salto de
  columna (8n bytes) no está alineado a página. Responde si el exponente medido
  del clásico (p ≈ 3,5 en vez de 3) se debe a la capacidad de la caché o a los
  **conflictos de conjunto** que produce un stride potencia de dos: con n = 1000
  el costo por operación es 6× menor que con n = 1024 pese a ocupar la misma
  memoria, así que la causa es el alineamiento, no la capacidad. Es el
  resultado que reinterpreta la comparación clásico/Strassen en el informe.
  Resultado en `data/measurements/matrix_stride_check.csv`.
- **`scripts/plot_generator.py`** — produce `matrix_time_vs_n.png`,
  `matrix_time_dense.png`, `matrix_normalized.png`, `matrix_speedup.png`,
  `matrix_memory_vs_n.png`, `matrix_type_effect.png`,
  `matrix_cutoff_sweep.png`, `matrix_stride_check.png`, las tablas
  `table_matrix_*.tex` y las macros `numbers_matrix.tex`.

---

## 5. Ordenamiento de arreglo unidimensional

### 5.1. Algoritmos

| Archivo | Algoritmo | Tiempo (mejor / promedio / peor) | Memoria auxiliar |
|---|---|---|---|
| `algorithms/sort.cpp` | `std::sort` (introsort) | Θ(n log n) / Θ(n log n) / O(n log n) | Θ(1) |
| `algorithms/mergesort.cpp` | Merge sort top-down | Θ(n log n) en todos los casos | Θ(n) |
| `algorithms/quicksort.cpp` | Quick sort, Hoare + mediana de tres | Θ(n log n) / Θ(n log n) / Θ(n²) | Θ(1) |
| `algorithms/patiencesort.cpp` | Patience sort + mezcla k-vías | Θ(n) / Θ(n log k) / Θ(n log n) | Θ(n) |

Decisiones de implementación, documentadas en la cabecera de cada archivo:

- **Quick sort** usa **partición de Hoare** con pivote **mediana de tres** y
  recursión sobre el subarreglo más pequeño. Las tres cosas importan para este
  experimento: con pivote ingenuo las entradas ya ordenadas caerían en el peor
  caso Θ(n²) —para n = 10⁷ eso son ~10¹⁴ operaciones, imposible de medir—, y con
  partición de Lomuto el dominio D1 (solo 10 valores distintos, es decir ~10⁶
  repeticiones de cada valor cuando n = 10⁷) también degeneraría a Θ(n²).
- **Merge sort** usa **un único buffer auxiliar** reservado una sola vez, y
  **omite a propósito** el atajo «si las dos mitades ya están en orden, no
  mezclar»: sin él el algoritmo hace exactamente el mismo trabajo con cualquier
  permutación, lo que permite contrastar su Θ(n log n) independiente de los
  datos con quick sort y patience sort, que sí son sensibles al orden inicial.
- **Patience sort** representa las pilas con **punteros hacia abajo** (dos
  arreglos planos de n enteros) en lugar de `vector<vector<int>>`. Con la
  entrada ascendente del dominio D7 se generan k ≈ n = 10⁷ pilas; un
  `std::vector` por pila costaría más de 500 MB solo en cabeceras y millones de
  llamadas a `malloc`. La segunda fase mezcla las k pilas con un min-heap.

### 5.2. Firma común: la del `sort.cpp` entregado

`sort.cpp` se entrega con el material y **se conserva sin modificar** (sólo se
le antepone la cabecera de documentación que exige el punto 2.1(4)). Su firma es

```cpp
std::vector<int> sortArray(std::vector<int>& arr);
```

y las tres implementaciones propias adoptan exactamente la misma, para que el
programa principal las invoque de manera uniforme a través de un puntero a
función.

Consecuencia que hay que tener presente al leer las mediciones: la sentencia
`return arr;` de esa firma construye una **copia de n enteros en cada llamada**
(no puede elidirse por RVO/NRVO al construirse desde un parámetro por
referencia). La copia es idéntica para los cuatro algoritmos y queda dentro de
la región medida, así que:

- en **tiempo** añade un término Θ(n) igual para todos, despreciable frente al
  Θ(n log n) del ordenamiento;
- en **memoria** añade 4n bytes al pico de los algoritmos cuya memoria auxiliar
  sigue viva en el momento del `return` (`std::sort` y quick sort muestran
  exactamente 4n = sólo la copia; merge sort 8n = búfer + copia), mientras que
  en patience sort el pico ocurre antes del `return` y la copia no lo eleva.

El informe presenta los valores medidos tal cual y explica esta descomposición.

### 5.3. Programa principal — `sorting.cpp`

Recorre `data/array_input/`, ejecuta los cuatro algoritmos sobre cada caso,
**verifica** que la salida coincida con la de `std::sort`, escribe el arreglo
ordenado en `data/array_output/{base}_out.txt` y agrega una fila por medición al
CSV.

> El programa escribe los **72 archivos `_out.txt`** que exige el anexo A.1,
> incluidos los 18 casos con n = 10⁷ (858 MB en total); en la entrega reducida
> sólo se incluyen los 54 con n ≤ 10⁵ (véase la nota del inicio). Si sólo
> interesan las mediciones, la opción `--max-output-n N` omite la escritura
> para n > N y `--no-output` la desactiva por completo:
>
> ```bash
> make run RUN_ARGS="--max-output-n 100000"
> ```

### 5.4. Scripts

- **`scripts/array_generator.py`** — genera los arreglos del anexo A.1.
- **`scripts/plot_generator.py`** — produce `sorting_time_vs_n.png`,
  `sorting_time_random_D7.png`, `sorting_normalized_nlogn.png`,
  `sorting_memory_vs_n.png`, `sorting_input_type_effect.png`,
  `sorting_speedup_vs_stdsort.png`, las tablas `table_sorting_*.tex` y las
  macros `numbers_sorting.tex`.

---

## 6. Metodología de medición

Ambos programas miden igual, usando `common/benchmark.{hpp,cpp}`.

### 6.1. Tiempo

- Reloj `std::chrono::steady_clock`: **monótono**, así que no se ve afectado por
  ajustes del reloj del sistema (NTP, cambio de horario) que podrían producir
  saltos negativos.
- **Solo se cronometra la llamada al algoritmo.** La lectura de los archivos, la
  copia del arreglo, la verificación de correctitud y la escritura de la salida
  quedan fuera: para n = 10⁷ la E/S tarda más que el propio ordenamiento y
  enmascararía por completo el comportamiento asintótico.
- **Temporización por lotes.** Con n = 10 una ejecución dura ~30 ns, por debajo
  de la resolución del reloj (~100 ns), y medirla directamente solo entrega
  ceros. Por eso, cuando el caso es pequeño se preparan `batch` copias del
  arreglo **antes** de arrancar el cronómetro, se procesan las `batch` copias
  dentro de la región medida y se divide el total. El tamaño del lote se
  registra en la columna `batch` del CSV, de modo que la medición es auditable.
- **Repeticiones**: 15 / 7 / 3 según el tamaño del caso. Se registra **cada
  repetición por separado**, no un promedio, para conservar la evidencia cruda;
  el script de gráficos calcula la mediana y el rango intercuartílico.
- El estadístico de resumen es la **mediana**, no la media: el ruido del sistema
  operativo (planificación, interrupciones, migración entre núcleos) produce
  valores atípicos altos pero nunca bajos, y la mediana es robusta frente a esa
  asimetría.

### 6.2. Memoria

Se reportan dos métricas complementarias:

- **`peak_heap_bytes`** — pico de memoria dinámica **auxiliar**, obtenido
  reemplazando los operadores globales `new`/`delete` por versiones que llevan
  la cuenta exacta de bytes vivos y su máximo. Es la métrica principal porque
  mide justo lo que predice la teoría. Es exacta, determinista y portable.
  *Limitación asumida:* no contabiliza la pila de llamadas, de modo que el
  Θ(log n) de recursión de quick sort no aparece.
- **`peak_rss_bytes`** — pico de memoria residente del proceso completo
  (`GetProcessMemoryInfo` en Windows, `getrusage` en POSIX). Incluye el
  ejecutable, las pilas y los datos de entrada; sirve de contraste, pero su
  granularidad es de página y es monótona no decreciente.

La memoria se mide en **una ejecución aislada**, fuera del bucle de
repeticiones y sin lote: encadenar ejecuciones solaparía la memoria de una con
la de la siguiente y duplicaría artificialmente el pico. Repetirla no aportaría
nada porque el consumo es determinista, así que el mismo valor se replica en las
filas de todas las repeticiones del CSV.

### 6.3. Verificación de correctitud

Ninguna medición se acepta a ciegas:

- **Ordenamiento**: la salida de cada algoritmo se compara elemento a elemento
  con la de `std::sort` sobre la misma entrada.
- **Matrices**: el resultado de Strassen se compara coeficiente a coeficiente
  con el del método clásico.

El veredicto se guarda en la columna `correct` de cada fila del CSV, los
programas devuelven código de salida distinto de cero si alguna verificación
falla, y el script de gráficos avisa si encuentra filas marcadas como
incorrectas.

### 6.4. Reproducibilidad

- Los casos de prueba se generan con los scripts **entregados con el material,
  sin modificar** (`array_generator.py`, `matrix_generator.py`). No fijan
  semilla aleatoria, así que cada `make data` produce valores distintos de la
  misma distribución. Los archivos de datos incluidos en la entrega son los
  que efectivamente se midieron; los 36 de ordenamiento con n = 10⁷ no se
  incluyen por el límite de tamaño (nota del inicio) y no pueden reproducirse
  exactamente, sólo regenerarse con la misma estructura y distribución.
- Se compila con `-O2` y **sin** `-march=native`: esta última ata el binario al
  procesador exacto de la máquina y haría irreproducible el experimento en otro
  equipo.
- Toda figura, toda tabla y toda cifra citada en la prosa del informe se
  generan con los scripts de `scripts/` a partir de los CSV (las cifras, como
  macros `\newcommand` en `numbers_*.tex`). No hay ningún número escrito a
  mano en el informe.

---

## 7. Formato de los archivos

### Entradas

| Archivo | Formato |
|---|---|
| `data/array_input/{n}_{t}_{d}_{m}.txt` | los n enteros en **una sola línea**, separados por espacios |
| `data/matrix_input/{n}_{t}_{d}_{m}_{1,2}.txt` | **una fila por línea**, coeficientes separados por espacios |

donde, según el anexo A del enunciado:

- **Ordenamiento**: `n ∈ {10¹, 10³, 10⁵, 10⁷}`, `t ∈ {ascendente, descendente,
  aleatorio}`, `d ∈ {D1, D7}` (dominios `{0..9}` y `{0..10⁷}`), `m ∈ {a, b, c}`.
- **Matrices**: `n ∈ {2⁴, 2⁶, 2⁸, 2¹⁰}`, `t ∈ {dispersa, diagonal, densa}`,
  `d ∈ {D0, D10}` (dominios `{0,1}` y `{0..9}`), `m ∈ {a, b, c}`.

Las salidas (`*_out.txt`) usan el mismo formato que la entrada correspondiente.

### Mediciones

`data/measurements/sorting_measurements.csv`:

```
algorithm,n,type,domain,sample,rep,batch,time_ms,peak_heap_bytes,peak_rss_bytes,correct
```

`data/measurements/matrix_multiplication_measurements.csv`: las mismas columnas
más `cutoff` antes de `correct`.

---

## 8. Archivos entregados con el material

Los tres archivos de código que venían con contenido en el material se
conservan **con su código original sin modificar**. Lo único que se les
antepone es el comentario de documentación (identificación y referencias) que
exige el punto 2.1(4) del enunciado:

| Archivo | Código | Notas |
|---|---|---|
| `sorting/algorithms/sort.cpp` | original | su firma es la que adoptan las otras tres implementaciones (§5.2) |
| `sorting/scripts/array_generator.py` | original | escribe en `../data/array_input`, por eso `make data` lo ejecuta desde `scripts/` |
| `matrix_multiplication/scripts/matrix_generator.py` | original | ídem con `../data/matrix_input` |

`report/preamble.tex` y `report/report.tex` tampoco se modificaron, como exige
`report/README.md`.

---

## 9. Referencias

Cada archivo fuente lleva en su cabecera las referencias específicas usadas para
implementar ese algoritmo. Las principales:

- Cormen, T., Leiserson, C., Rivest, R., Stein, C. *Introduction to Algorithms*,
  3.ª ed., MIT Press, 2009.
- Knuth, D. E. *The Art of Computer Programming, Vol. 3: Sorting and Searching*,
  2.ª ed., Addison-Wesley, 1998.
- Hoare, C. A. R. «Quicksort», *The Computer Journal* 5(1), 1962.
- Sedgewick, R. «Implementing Quicksort Programs», *CACM* 21(10), 1978.
- Musser, D. R. «Introspective Sorting and Selection Algorithms», *SP&E* 27(8),
  1997.
- Mallows, C. L. «Patience sorting», *SIAM Review* 5(4), 1963.
- Aldous, D., Diaconis, P. «Longest increasing subsequences: from patience
  sorting to the Baik–Deift–Johansson theorem», *Bull. AMS* 36(4), 1999.
- Chandramouli, B., Goldstein, J. «Patience is a Virtue: Revisiting Merge and
  Sort on Modern Processors», *SIGMOD*, 2014.
- Strassen, V. «Gaussian elimination is not optimal», *Numerische Mathematik*
  13, 1969.
- Huss-Lederman, S. et al. «Implementation of Strassen's Algorithm for Matrix
  Multiplication», *Supercomputing '96*.
- McGeoch, C. C. *A Guide to Experimental Algorithmics*, Cambridge University
  Press, 2012.
