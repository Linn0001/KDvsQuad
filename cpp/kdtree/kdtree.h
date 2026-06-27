#ifndef KDVSQUAD_CPP_KDTREE_KDTREE_H
#define KDVSQUAD_CPP_KDTREE_KDTREE_H

#include <vector>
#include <string>
#include <queue>
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <functional>
#include <utility>

namespace spatial {

static constexpr double EARTH_RADIUS_KM = 6371.0;

inline double to_rad(double deg) {
    return deg * M_PI / 180.0;
}

inline double haversine(double lat1, double lon1, double lat2, double lon2) {
    double dphi = to_rad(lat2 - lat1);
    double dlambda = to_rad(lon2 - lon1);
    double phi1 = to_rad(lat1);
    double phi2 = to_rad(lat2);
    double a = std::sin(dphi / 2) * std::sin(dphi / 2)
             + std::cos(phi1) * std::cos(phi2)
             * std::sin(dlambda / 2) * std::sin(dlambda / 2);
    return EARTH_RADIUS_KM * 2.0 * std::atan2(std::sqrt(a), std::sqrt(1.0 - a));
}

struct POI {
    long long   id;
    std::string name;
    std::string category;
    double      lat;
    double      lon;
};

struct QueryResult {
    POI    poi;
    double distance_km;

    bool operator<(const QueryResult& o) const {
        return distance_km < o.distance_km;
    }
};

struct KDNode {
    POI     poi;
    int     axis;
    KDNode* left  = nullptr;
    KDNode* right = nullptr;

    KDNode(const POI& p, int ax) : poi(p), axis(ax) {}
};

class KDTree {
public:
    explicit KDTree(std::vector<POI> points)
        : size_(points.size()), root_(build(points, 0, points.size(), 0)) {}

    ~KDTree() { destroy(root_); }

    KDTree(const KDTree&)            = delete;
    KDTree& operator=(const KDTree&) = delete;
    KDTree(KDTree&&)                 = default;

    std::size_t size() const { return size_; }

    std::vector<QueryResult> knn_query(double lat, double lon, int k) const {
        if (k <= 0) throw std::invalid_argument("k debe ser mayor que 0");

        MaxHeap heap;
        knn_search(root_, lat, lon, k, heap);

        std::vector<QueryResult> results;
        results.reserve(heap.size());
        while (!heap.empty()) {
            auto [dist, node] = heap.top(); heap.pop();
            results.push_back({node->poi, dist});
        }
        std::sort(results.begin(), results.end());
        return results;
    }

    std::vector<QueryResult> range_query(double lat, double lon, double radius_km) const {
        if (radius_km <= 0) throw std::invalid_argument("radio debe ser mayor que 0");

        std::vector<QueryResult> results;
        range_search(root_, lat, lon, radius_km, results);
        std::sort(results.begin(), results.end());
        return results;
    }

private:
    std::size_t size_;
    KDNode*     root_;

    KDNode* build(std::vector<POI>& pts, std::size_t lo, std::size_t hi, int depth) {
        if (lo >= hi) return nullptr;

        int axis = depth % 2;
        std::size_t mid = lo + (hi - lo) / 2;

        std::nth_element(
            pts.begin() + lo,
            pts.begin() + mid,
            pts.begin() + hi,
            [axis](const POI& a, const POI& b) {
                return axis == 0 ? a.lat < b.lat : a.lon < b.lon;
            }
        );

        KDNode* node  = new KDNode(pts[mid], axis);
        node->left    = build(pts, lo,      mid,  depth + 1);
        node->right   = build(pts, mid + 1, hi,   depth + 1);
        return node;
    }

    void destroy(KDNode* node) {
        if (!node) return;
        destroy(node->left);
        destroy(node->right);
        delete node;
    }

    using HeapPair = std::pair<double, KDNode*>;
    struct MaxCmp {
        bool operator()(const HeapPair& a, const HeapPair& b) const {
            return a.first < b.first;
        }
    };
    using MaxHeap = std::priority_queue<HeapPair, std::vector<HeapPair>, MaxCmp>;

    void knn_search(KDNode* node, double lat, double lon, int k, MaxHeap& heap) const {
        if (!node) return;

        double dist = haversine(lat, lon, node->poi.lat, node->poi.lon);

        if ((int)heap.size() < k) {
            heap.push({dist, node});
        } else if (dist < heap.top().first) {
            heap.pop();
            heap.push({dist, node});
        }

        knn_search(node->left,  lat, lon, k, heap);
        knn_search(node->right, lat, lon, k, heap);
    }

    void range_search(KDNode* node, double lat, double lon,
                      double radius_km, std::vector<QueryResult>& results) const {
        if (!node) return;

        double dist = haversine(lat, lon, node->poi.lat, node->poi.lon);
        if (dist <= radius_km) {
            results.push_back({node->poi, dist});
        }

        range_search(node->left,  lat, lon, radius_km, results);
        range_search(node->right, lat, lon, radius_km, results);
    }
};


} // namespace spatial

#endif // KDVSQUAD_CPP_KDTREE_KDTREE_H
