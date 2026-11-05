"""Analista de límites departamentales: une geometría (MGN) con nombres (DIVIPOLA).

La llave es el código DANE de 2 dígitos (DPTO_CCDGO / cod_dpto), nunca el nombre.
Salida: GeoJSON con propiedades {codigo, nombre} y un miembro extra "metadatos"
(GeoJSON permite miembros adicionales en el FeatureCollection; Leaflet los ignora).
"""

from pathlib import Path

from agents.comun.archivos import ahora_utc, escribir_json, leer_json
from agents.comun.resultado import Resultado
from agents.comun.rutas import PROCESSED
from agents.recolector.dane_departamentos import RUTA_GEOMETRIA, RUTA_NOMBRES

RUTA_SALIDA = PROCESSED / "departamentos.geojson"


def unir(geojson: dict, divipola: list[dict]) -> dict:
    nombres = {fila["cod_dpto"]: fila["dpto"] for fila in divipola}
    features = []
    faltantes = []
    for f in geojson["features"]:
        codigo = f["properties"]["DPTO_CCDGO"]
        if codigo not in nombres:
            faltantes.append(codigo)
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"codigo": codigo, "nombre": nombres[codigo]},
                "geometry": f["geometry"],
            }
        )
    if faltantes:
        raise ValueError(f"Departamentos sin nombre en DIVIPOLA: {faltantes}")
    features.sort(key=lambda f: f["properties"]["codigo"])
    return {"type": "FeatureCollection", "features": features}


def ejecutar(
    geometria: Path = RUTA_GEOMETRIA, nombres: Path = RUTA_NOMBRES, destino: Path = RUTA_SALIDA
) -> Resultado:
    meta_geo = leer_json(geometria.with_name(geometria.name + ".meta.json"))
    meta_nom = leer_json(nombres.with_name(nombres.name + ".meta.json"))
    salida = unir(leer_json(geometria), leer_json(nombres))
    salida["metadatos"] = {
        "fuentes": [meta_geo, meta_nom],
        "procesado_en": ahora_utc(),
        "notas": (
            "Geometría simplificada en el servidor del DANE (tolerancia 0.01°, ~1,1 km): "
            "apta para visualización, no para cálculos de área."
        ),
    }
    escribir_json(destino, salida, compacto=True)
    return Resultado(
        "analista.departamentos", f"{len(salida['features'])} departamentos con nombre", [destino]
    )
