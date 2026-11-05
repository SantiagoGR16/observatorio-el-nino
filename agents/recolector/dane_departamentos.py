"""Recolector de límites departamentales (DANE, Marco Geoestadístico Nacional 2025).

Hechos verificados (2026-11-04):
- Geometría: FeatureServer del MGN 2025, capa 319 "Departamento". El MapServer de la
  misma capa devuelve geometry=null en GeoJSON; el FeatureServer sí la trae.
- `where=1=1` responde con una página de error (probable filtro anti-inyección SQL);
  se usa `OBJECTID>0`.
- Simplificación en servidor: maxAllowableOffset=0.01° (~1,1 km) da 33 departamentos y
  ~130 KB. Con 0.005 el servidor responde HTTP 500.
- Los nombres llegan con la tilde dañada desde el servidor ("BOGOT�"), así que los
  nombres se toman de DIVIPOLA en datos.gov.co y se unen por código DANE.

Los límites casi no cambian: solo se descargan si faltan o tienen más de 90 días.
"""

import json
import time
from pathlib import Path

import requests

from agents.comun.archivos import ahora_utc, guardar_crudo
from agents.comun.http import TIMEOUT_S, crear_sesion
from agents.comun.resultado import Resultado
from agents.comun.rutas import RAW

URL_MGN = (
    "https://geoportal.dane.gov.co/mparcgis/rest/services/"
    "MGN2025/Serv_CapasMGN_2025/FeatureServer/319/query"
)
PARAMS_MGN = {
    "where": "OBJECTID>0",
    "outFields": "DPTO_CCDGO,DPTO_CNMBRE",
    "outSR": "4326",
    "maxAllowableOffset": "0.01",
    "geometryPrecision": "4",
    "f": "geojson",
}
# DIVIPOLA (DANE) publicada en datos.gov.co vía API Socrata.
URL_DIVIPOLA = "https://www.datos.gov.co/resource/gdxc-w37w.json"
PARAMS_DIVIPOLA = {
    "$select": "cod_dpto,dpto",
    "$group": "cod_dpto,dpto",
    "$order": "cod_dpto",
    "$limit": "100",
}

DIR_DANE = RAW / "dane"
RUTA_GEOMETRIA = DIR_DANE / "departamentos_mgn2025.geojson"
RUTA_NOMBRES = DIR_DANE / "divipola_departamentos.json"
MAX_EDAD_DIAS = 90


def _vigente(ruta: Path) -> bool:
    return ruta.exists() and (time.time() - ruta.stat().st_mtime) < MAX_EDAD_DIAS * 86400


def ejecutar(
    base: Path = DIR_DANE, sesion: requests.Session | None = None, forzar: bool = False
) -> Resultado:
    geometria, nombres = base / RUTA_GEOMETRIA.name, base / RUTA_NOMBRES.name
    if not forzar and _vigente(geometria) and _vigente(nombres):
        return Resultado(
            "recolector.dane_departamentos",
            "DANE: límites en caché (< 90 días)",
            [geometria, nombres],
        )

    sesion = sesion or crear_sesion()
    resp = sesion.get(URL_MGN, params=PARAMS_MGN, timeout=TIMEOUT_S * 3)
    resp.raise_for_status()
    datos = resp.json()  # falla aquí si el servidor devolvió una página HTML de error
    sin_geom = [f["properties"] for f in datos["features"] if f["geometry"] is None]
    if not datos["features"] or sin_geom:
        raise ValueError(f"MGN sin geometría para: {sin_geom or 'todos'}")
    guardar_crudo(
        geometria,
        resp.content,
        {
            "fuente": "DANE — Marco Geoestadístico Nacional 2025, capa Departamento",
            "url": URL_MGN,
            "parametros": PARAMS_MGN,
            "descargado_en": ahora_utc(),
        },
    )

    resp = sesion.get(URL_DIVIPOLA, params=PARAMS_DIVIPOLA, timeout=TIMEOUT_S)
    resp.raise_for_status()
    json.loads(resp.content)  # valida que sea JSON
    guardar_crudo(
        nombres,
        resp.content,
        {
            "fuente": "DANE — DIVIPOLA en datos.gov.co (dataset gdxc-w37w)",
            "url": URL_DIVIPOLA,
            "parametros": PARAMS_DIVIPOLA,
            "descargado_en": ahora_utc(),
        },
    )
    return Resultado(
        "recolector.dane_departamentos",
        f"DANE: {len(datos['features'])} departamentos descargados",
        [geometria, nombres],
    )
