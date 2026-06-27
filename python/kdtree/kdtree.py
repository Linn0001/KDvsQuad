from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def euclidean(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


@dataclass
class KDNode:
    lat: float
    lon: float
    data: Any
    axis: int
    left: KDNode | None = field(default=None, repr=False)
    right: KDNode | None = field(default=None, repr=False)


class KDTree:
    def __init__(self, points: list[dict]):
        self.size = len(points)
        self.root = self._build(points, depth=0)

    def _build(self, points: list[dict], depth: int) -> KDNode | None:
        if not points:
            return None

        axis = depth % 2
        key = "lat" if axis == 0 else "lon"

        points.sort(key=lambda p: p[key])
        mid = len(points) // 2
        p = points[mid]

        node = KDNode(
            lat=p["lat"],
            lon=p["lon"],
            data={k: v for k, v in p.items() if k not in ("lat", "lon")},
            axis=axis,
        )
        node.left = self._build(points[:mid], depth + 1)
        node.right = self._build(points[mid + 1:], depth + 1)
        return node

    def knn_query(self, lat: float, lon: float, k: int = 1) -> list[dict]:
        best: list[tuple[float, KDNode]] = []

        def search(node: KDNode | None):
            if node is None:
                return

            dist = haversine(lat, lon, node.lat, node.lon)

            if len(best) < k:
                best.append((dist, node))
                best.sort(key=lambda x: x[0])
            elif dist < best[-1][0]:
                best[-1] = (dist, node)
                best.sort(key=lambda x: x[0])

            diff = (lat - node.lat) if node.axis == 0 else (lon - node.lon)
            near, far = (node.left, node.right) if diff <= 0 else (node.right, node.left)

            search(near)

            plane_dist = haversine(lat, lon,
                                   node.lat if node.axis == 1 else lat,
                                   node.lon if node.axis == 0 else lon)
            if len(best) < k or plane_dist < best[-1][0]:
                search(far)

        search(self.root)

        return [
            {"lat": n.lat, "lon": n.lon, "distance_km": d, **n.data}
            for d, n in best
        ]

    def range_query(self, lat: float, lon: float, radius_km: float) -> list[dict]:
        results: list[tuple[float, KDNode]] = []

        def search(node: KDNode | None):
            if node is None:
                return

            dist = haversine(lat, lon, node.lat, node.lon)
            if dist <= radius_km:
                results.append((dist, node))

            diff = (lat - node.lat) if node.axis == 0 else (lon - node.lon)
            near, far = (node.left, node.right) if diff <= 0 else (node.right, node.left)

            search(near)

            plane_dist = haversine(lat, lon,
                                   node.lat if node.axis == 1 else lat,
                                   node.lon if node.axis == 0 else lon)
            if plane_dist <= radius_km:
                search(far)

        search(self.root)
        results.sort(key=lambda x: x[0])

        return [
            {"lat": n.lat, "lon": n.lon, "distance_km": d, **n.data}
            for d, n in results
        ]

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return f"KDTree(size={self.size})"