# KD-Tree vs Quadtree

**CS3014 – Estructura de Datos Avanzados | Proyecto Final 2026-1**

Comparación de rendimiento entre estructuras de datos espaciales para la búsqueda de Puntos de Interés (POI) en datos de mapas reales, inspirado en un Google Maps simplificado. Comparamos el rendimiento de KD-Trees y Quadtrees, además comparamos sus respectivas implementaciones en Python y C++, evaluando tiempo de construcción, consultas KNN y consultas por rango a escala.

---

## Integrantes

- Sergio Delgado    — 202310227
- Jhon Chilo        — 202310364
- Ariana Mercado    — 202310179

---

## Planteamiento del Problema

Dado un conjunto de datos de millones de restaurantes y puntos de interés (obtenidos de OpenStreetMap), responder eficientemente:

- **Consultas KNN** — *"Encuentra los 5 restaurantes más cercanos a mi ubicación"*
- **Consultas por rango** — *"Encuentra todos los POIs dentro de 2 km de este punto"*

Comparamos dos estructuras de datos espaciales (KD-Tree y Quadtree) y dos implementaciones en distintos lenguajes (Python y C++) para analizar los compromisos en tiempo de construcción, velocidad de consulta y uso de memoria.

---

## Estructura pensada (xfa vamos editando esto poco a poco)

```
KDVSQUAD/
│
├── cpp/
│   ├── kdtree/       # Implementación del KD-Tree
│   │   ├── kdtree.cpp
│   │   └── main.cpp          # Punto de entrada para benchmarks
│   └── quadtree/
│
├── python/
│   ├── kdtree/
│   │   ├── kdtree.py         # Implementación del KD-Tree
│   └── quadtree/
│
├── bm/
│   └── results.csv           # Resultados de tiempos de construcción y consulta
│
├── pdfs/
│   └── report.pdf
│
└── README.md
└── Instr.md                  # Instrucciones para descargar el dataset
└── sample_1k.csv             # por mientras
└── script.py
```

---

## Dependencias

### Python
- Python 3.10+
- `numpy` — operaciones con arreglos
- `matplotlib` — graficado de resultados
- `pandas` — carga del dataset

```bash
pip install numpy matplotlib pandas
```

### C++
- C++17 o superior
- `g++` o `clang++`
- CMake 3.15+ (opcional, para sistema de build)

```bash
# Compilar directamente con g++
g++ -O2 -std=c++17 cpp/kdtree/main.cpp -o kdtree_bench
```

---

## Dataset

Usamos datos de POIs de **OpenStreetMap** a través de la [API de Overpass](https://overpass-api.de/) o datasets pre-exportados de [GeoFabrik](https://download.geofabrik.de/).

Se incluye una muestra pequeña (`data/sample_1k.csv`) para pruebas rápidas. Para los benchmarks completos, descarga el dataset siguiendo las instrucciones en `data/README.md`.

Formato esperado del CSV:

```
id,name,lat,lon,category
1,McDonald's,-12.0464,-77.0428,restaurant
2,KFC,-12.1091,-77.0365,restaurant
...
```

---

## Cómo Ejecutar

### Python — Benchmark KD-Tree

```bash
cd python/kdtree
python benchmark.py --input ../../data/sample_1k.csv --k 5 --radius 0.05
```

### C++ — Benchmark KD-Tree

```bash
g++ -O2 -std=c++17 cpp/kdtree/main.cpp -o kdtree_bench
./kdtree_bench --input data/sample_1k.csv --k 5 --radius 0.05
```

Ambos scripts muestran el tiempo de construcción, el tiempo promedio de consulta KNN y el tiempo promedio de consulta por rango.

## Referencias

- de Berg et al., *Computational Geometry: Algorithms and Applications*, 3ra ed.
- Samet, H., *Foundations of Multidimensional and Metric Data Structures*
- Colaboradores de OpenStreetMap — [openstreetmap.org](https://www.openstreetmap.org)
- Bentley, J.L. (1975). *Multidimensional binary search trees used for associative searching.* CACM.
