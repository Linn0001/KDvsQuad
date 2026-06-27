import json
import csv
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_geojson(input_path: Path) -> list[dict]:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    pois = []

    for i, feat in enumerate(features):
        geometry = feat.get("geometry", {})
        if geometry.get("type") != "Point":
            continue

        coords = geometry.get("coordinates", [])
        if len(coords) < 2:
            continue

        lon, lat = coords[0], coords[1]
        props = feat.get("properties", {})

        name = props.get("name") or props.get("name:es") or "Sin nombre"
        category = (
            props.get("amenity") or
            props.get("shop") or
            props.get("tourism") or
            "unknown"
        )

        raw_id = str(props.get("@id", i))
        clean_id = raw_id.split("/")[-1]

        pois.append({
            "id": clean_id,
            "name": name,
            "lat": lat,
            "lon": lon,
            "category": category,
        })

    return pois


def parse_overpass_json(input_path: Path) -> list[dict]:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    pois = []

    for elem in elements:
        if elem.get("type") != "node":
            continue
        lat = elem.get("lat")
        lon = elem.get("lon")
        if lat is None or lon is None:
            continue

        tags = elem.get("tags", {})
        name = tags.get("name", "Sin nombre")
        category = tags.get("amenity") or tags.get("shop") or tags.get("tourism") or "unknown"

        pois.append({
            "id": elem.get("id"),
            "name": name,
            "lat": lat,
            "lon": lon,
            "category": category,
        })

    return pois


def parse_osm_xml(input_path: Path) -> list[dict]:
    tree = ET.parse(input_path)
    root = tree.getroot()

    pois = []

    for node in root.iter("node"):
        lat = node.get("lat")
        lon = node.get("lon")
        if lat is None or lon is None:
            continue

        tags = {tag.get("k"): tag.get("v") for tag in node.iter("tag")}

        category = tags.get("amenity") or tags.get("shop") or tags.get("tourism")
        if not category:
            continue

        name = tags.get("name", "Sin nombre")

        pois.append({
            "id": node.get("id"),
            "name": name,
            "lat": float(lat),
            "lon": float(lon),
            "category": category,
        })

    return pois


def write_csv(pois: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "lat", "lon", "category"])
        writer.writeheader()
        writer.writerows(pois)


def main():
    parser = argparse.ArgumentParser(
        description="Convierte datos OSM (JSON o XML) al formato CSV del proyecto."
    )
    parser.add_argument(
        "--input",  "-i",
        required=True,
        help="Ruta al archivo de entrada (.json de Overpass o .osm de osmfilter)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Ruta al archivo CSV de salida"
    )
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[ERROR] No se encontró el archivo: {input_path}")
        return

    suffix = input_path.suffix.lower()

    print(f"[INFO] Leyendo {input_path} ...")

    if suffix == ".geojson":
        pois = parse_geojson(input_path)
    elif suffix == ".json":
        pois = parse_overpass_json(input_path)
    elif suffix == ".osm":
        pois = parse_osm_xml(input_path)
    else:
        print(f"[ERROR] Formato no soportado: '{suffix}'. Usa .geojson, .json o .osm")
        return

    if not pois:
        print("[ADVERTENCIA] No se encontraron POIs en el archivo.")
        return

    write_csv(pois, output_path)

    print(f"[OK] {len(pois):,} POIs guardados en {output_path}")


if __name__ == "__main__":
    main()