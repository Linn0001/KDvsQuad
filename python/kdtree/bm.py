import time
import csv
import argparse
import subprocess
import re
import random
from pathlib import Path

from kdtree import KDTree

def load_csv(path: str) -> list[dict]:
    pois = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pois.append({
                    "id":       row["id"],
                    "name":     row["name"],
                    "lat":      float(row["lat"]),
                    "lon":      float(row["lon"]),
                    "category": row["category"],
                })
            except (ValueError, KeyError):
                continue
    return pois

def benchmark_python(pois: list[dict], query_points: list[tuple],
                     k: int, radius: float) -> dict:
    t0 = time.perf_counter()
    tree = KDTree(pois)
    build_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for lat, lon in query_points:
        tree.knn_query(lat, lon, k)
    knn_ms = (time.perf_counter() - t0) * 1000 / len(query_points)

    t0 = time.perf_counter()
    total_found = 0
    for lat, lon in query_points:
        total_found += len(tree.range_query(lat, lon, radius))
    range_ms = (time.perf_counter() - t0) * 1000 / len(query_points)

    return {
        "build_ms":    build_ms,
        "knn_ms":      knn_ms,
        "range_ms":    range_ms,
        "total_found": total_found,
    }

def benchmark_cpp(input_path: str, k: int, radius: float,
                  queries: int, binary: str) -> dict | None:
    binary_path = Path(binary)
    if not binary_path.exists():
        return None

    cmd = [
        str(binary_path),
        "--input",   input_path,
        "--k",       str(k),
        "--radius",  str(radius),
        "--queries", str(queries),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    def extract(pattern: str) -> float | None:
        m = re.search(pattern, output)
        return float(m.group(1)) if m else None

    build_ms = extract(r"Construcci[oó]n\s+([\d.]+)")
    knn_ms   = extract(r"KNN \(promedio\)\s+([\d.]+)")
    range_ms = extract(r"Range \(promedio\)\s+([\d.]+)")

    if None in (build_ms, knn_ms, range_ms):
        return None

    return {
        "build_ms": build_ms,
        "knn_ms":   knn_ms,
        "range_ms": range_ms,
    }

def print_table(py: dict, cpp: dict | None, k: int, radius: float,
                n_points: int, n_queries: int):

    def speedup(py_val: float, cpp_val: float) -> str:
        if cpp_val and cpp_val > 0:
            s = py_val / cpp_val
            return f"{s:.1f}x"
        return "—"

    def fmt(val: float | None) -> str:
        if val is None:
            return "—"
        if val < 0.01:
            return "< 0.01 ms"
        return f"{val:.2f} ms"

    COL = 20

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║            KD-Tree Benchmark: Python vs C++                 ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  POIs en dataset : {n_points:<10}                              ║")
    print(f"║  Consultas       : {n_queries:<10}                              ║")
    print(f"║  k (KNN)         : {k:<10}                              ║")
    print(f"║  Radio (range)   : {str(radius) + ' km':<10}                              ║")
    print("╠══════════════════════╦══════════════╦══════════════╦═════════╣")
    print("║  Operación           ║  Python      ║  C++         ║ Speedup ║")
    print("╠══════════════════════╬══════════════╬══════════════╬═════════╣")

    rows = [
        ("Construcción",   py["build_ms"], cpp["build_ms"] if cpp else None),
        (f"KNN (k={k})",   py["knn_ms"],   cpp["knn_ms"]   if cpp else None),
        (f"Range ({radius} km)", py["range_ms"], cpp["range_ms"] if cpp else None),
    ]

    for label, py_val, cpp_val in rows:
        su = speedup(py_val, cpp_val) if cpp_val is not None else "—"
        print(f"║  {label:<20}║  {fmt(py_val):<12}║  {fmt(cpp_val):<12}║  {su:<7}║")

    print("╚══════════════════════╩══════════════╩══════════════╩═════════╝")

    if cpp is None:
        print()
        print("  ⚠  Binario C++ no encontrado. Compilar con:")
        print("     g++ -O2 -std=c++17 ../../cpp/kdtree/main.cpp -o ../../cpp/kdtree/kdtree_bench")

    print()

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark comparativo KD-Tree Python vs C++"
    )
    parser.add_argument("--input",   "-i", default="../../data/sample_1k.csv",
                        help="CSV de POIs")
    parser.add_argument("--k",       "-k", type=int,   default=5,
                        help="Número de vecinos para KNN")
    parser.add_argument("--radius",  "-r", type=float, default=2.0,
                        help="Radio en km para range query")
    parser.add_argument("--queries", "-q", type=int,   default=100,
                        help="Número de consultas aleatorias")
    parser.add_argument("--binary",  "-b",
                        default="../../cpp/kdtree/kdtree_bench",
                        help="Ruta al binario C++ compilado")
    args = parser.parse_args()

    print(f"\n  Cargando {args.input} ...")
    pois = load_csv(args.input)
    if not pois:
        print("  [ERROR] No se encontraron POIs. Verifica el archivo CSV.")
        return
    print(f"  {len(pois):,} POIs cargados.\n")

    random.seed(42)
    query_points = [
        (p["lat"], p["lon"])
        for p in random.sample(pois, min(args.queries, len(pois)))
    ]

    print("  Corriendo benchmark Python ...")
    py_results = benchmark_python(pois, query_points, args.k, args.radius)

    print("  Corriendo benchmark C++ ...")
    cpp_results = benchmark_cpp(args.input, args.k, args.radius,
                                len(query_points), args.binary)

    print_table(
        py=py_results,
        cpp=cpp_results,
        k=args.k,
        radius=args.radius,
        n_points=len(pois),
        n_queries=len(query_points),
    )


if __name__ == "__main__":
    main()