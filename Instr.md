# Dataset — Instrucciones de Descarga

Este directorio contiene los datos de Puntos de Interés (POI) usados para los benchmarks del proyecto. Se incluye una muestra pequeña lista para usar; para los experimentos completos sigue las instrucciones de abajo.

---

## Archivos incluidos

| Archivo | Descripción |
|---|---|
| `sample_1k.csv` | Muestra de 1,000 POIs de Lima para pruebas rápidas |

---

## Overpass API

La [API de Overpass](https://overpass-api.de/) permite consultar OpenStreetMap directamente desde el navegador o por script.

### Paso 1 — Abre el editor de consultas

Ve a [overpass-turbo.eu](https://overpass-turbo.eu/) y pega la siguiente consulta para obtener restaurantes de Lima:

```
[out:json][timeout:60];
(
  node["amenity"="restaurant"](area["name"="Lima"]);
  node["amenity"="fast_food"](area["name"="Lima"]);
  node["amenity"="cafe"](area["name"="Lima"]);
);
out body;
```

Para más categorías (hoteles, farmacias, etc.) agrega líneas con otros valores de `amenity`. La lista completa está en el [wiki de OSM](https://wiki.openstreetmap.org/wiki/Key:amenity).

### Paso 2 — Exporta el resultado

En Overpass Turbo: **Exportar → GeoJSON** o **Exportar → Raw data → JSON**. (solo que sea json)

- Utilizar el script en este proyecto para convertirlo a csv

```bash
python script.py --input ./lima_raw.geojson --output ./lima_pois.csv
```

---

## Formato esperado del CSV

Todos los scripts del proyecto esperan este formato:

```
id,name,lat,lon,category
1,McDonald's,-12.0464,-77.0428,restaurant
2,KFC,-12.1091,-77.0365,fast_food
3,Starbucks,-12.1200,-77.0300,cafe
...
```

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | entero | Identificador único del POI |
| `name` | string | Nombre del local |
| `lat` | float | Latitud (grados decimales) |
| `lon` | float | Longitud (grados decimales) |
| `category` | string | Categoría OSM (`amenity`) |

---

## Tamaños de dataset para pruebas

| Experimento | Tamaño |
|---|---|
| Prueba rápida / desarrollo | 1K puntos (`sample_1k.csv`) |
| Benchmark Python vs C++ | 10K – 100K puntos |
| Benchmark final completo | 500K – 1M puntos |

