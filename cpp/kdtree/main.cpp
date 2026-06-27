#include "kdtree.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <random>
#include <stdexcept>
#include <iomanip>

using Clock    = std::chrono::high_resolution_clock;
using Ms       = std::chrono::duration<double, std::milli>;

double elapsed_ms(Clock::time_point start) {
    return Ms(Clock::now() - start).count();
}

std::vector<spatial::POI> load_csv(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open())
        throw std::runtime_error("No se pudo abrir el archivo: " + path);

    std::vector<spatial::POI> pois;
    std::string line;

    std::getline(file, line);

    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::istringstream ss(line);
        std::string id_s, name, lat_s, lon_s, category;

        std::getline(ss, id_s,     ',');
        std::getline(ss, name,     ',');
        std::getline(ss, lat_s,    ',');
        std::getline(ss, lon_s,    ',');
        std::getline(ss, category, ',');

        try {
            spatial::POI p;
            p.id       = std::stoll(id_s);
            p.name     = name;
            p.lat      = std::stod(lat_s);
            p.lon      = std::stod(lon_s);
            p.category = category;
            pois.push_back(p);
        } catch (...) {
        }
    }

    return pois;
}

struct Args {
    std::string input   = "data/sample_1k.csv";
    int         k       = 5;
    double      radius  = 2.0;
    int         queries = 100;
};

Args parse_args(int argc, char* argv[]) {
    Args args;
    for (int i = 1; i < argc - 1; ++i) {
        std::string flag = argv[i];
        std::string val  = argv[i + 1];
        if      (flag == "--input"   || flag == "-i") args.input   = val;
        else if (flag == "--k"       || flag == "-k") args.k       = std::stoi(val);
        else if (flag == "--radius"  || flag == "-r") args.radius  = std::stod(val);
        else if (flag == "--queries" || flag == "-q") args.queries = std::stoi(val);
    }
    return args;
}

int main(int argc, char* argv[]) {
    Args args = parse_args(argc, argv);

    std::cout << "================================================\n";
    std::cout << "  KD-Tree Benchmark — C++\n";
    std::cout << "================================================\n";
    std::cout << "  Archivo : " << args.input   << "\n";
    std::cout << "  k       : " << args.k       << "\n";
    std::cout << "  Radio   : " << args.radius  << " km\n";
    std::cout << "  Queries : " << args.queries << "\n";
    std::cout << "------------------------------------------------\n\n";

    std::cout << "[1/4] Cargando dataset...\n";
    auto t0 = Clock::now();
    std::vector<spatial::POI> pois;
    try {
        pois = load_csv(args.input);
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] " << e.what() << "\n";
        return 1;
    }
    std::cout << "      " << pois.size() << " POIs cargados en "
              << std::fixed << std::setprecision(2) << elapsed_ms(t0) << " ms\n\n";

    if (pois.empty()) {
        std::cerr << "[ERROR] El dataset está vacío.\n";
        return 1;
    }

    std::cout << "[2/4] Construyendo KD-Tree...\n";
    t0 = Clock::now();
    spatial::KDTree tree(pois);
    double build_ms = elapsed_ms(t0);
    std::cout << "      Árbol construido en "
              << std::fixed << std::setprecision(2) << build_ms << " ms\n\n";

    
    std::mt19937 rng(42);
    std::uniform_int_distribution<std::size_t> dist(0, pois.size() - 1);
    std::vector<std::pair<double,double>> query_points;
    query_points.reserve(args.queries);
    for (int i = 0; i < args.queries; ++i) {
        const auto& p = pois[dist(rng)];
        query_points.push_back({p.lat, p.lon});
    }
    std::cout << "[3/4] Benchmark KNN (k=" << args.k << ")...\n";
    t0 = Clock::now();
    std::size_t knn_total = 0;
    for (auto [lat, lon] : query_points) {
        auto res = tree.knn_query(lat, lon, args.k);
        knn_total += res.size();
    }
    double knn_total_ms = elapsed_ms(t0);
    double knn_avg_ms   = knn_total_ms / args.queries;
    std::cout << "      Total : " << std::fixed << std::setprecision(2) << knn_total_ms << " ms\n";
    std::cout << "      Promedio por consulta: " << knn_avg_ms << " ms\n\n";

    std::cout << "[4/4] Benchmark Range Query (r=" << args.radius << " km)...\n";
    t0 = Clock::now();
    std::size_t range_total = 0;
    for (auto [lat, lon] : query_points) {
        auto res = tree.range_query(lat, lon, args.radius);
        range_total += res.size();
    }
    double range_total_ms = elapsed_ms(t0);
    double range_avg_ms   = range_total_ms / args.queries;
    std::cout << "      Total : " << std::fixed << std::setprecision(2) << range_total_ms << " ms\n";
    std::cout << "      Promedio por consulta: " << range_avg_ms << " ms\n";
    std::cout << "      POIs encontrados (total): " << range_total << "\n\n";

    std::cout << "================================================\n";
    std::cout << "  RESUMEN\n";
    std::cout << "================================================\n";
    std::cout << std::left << std::setw(30) << "  Construcción"
              << std::right << std::setw(10) << build_ms     << " ms\n";
    std::cout << std::left << std::setw(30) << "  KNN (promedio)"
              << std::right << std::setw(10) << knn_avg_ms   << " ms\n";
    std::cout << std::left << std::setw(30) << "  Range (promedio)"
              << std::right << std::setw(10) << range_avg_ms << " ms\n";
    std::cout << "================================================\n";

    auto [qlat, qlon] = query_points[0];
    std::cout << "\n  Ejemplo KNN desde (" << qlat << ", " << qlon << "):\n";
    auto sample = tree.knn_query(qlat, qlon, std::min(args.k, 3));
    for (auto& r : sample) {
        std::cout << "    [" << r.poi.category << "] "
                  << r.poi.name << " — "
                  << std::fixed << std::setprecision(3)
                  << r.distance_km << " km\n";
    }
    std::cout << "\n";

    return 0;
}