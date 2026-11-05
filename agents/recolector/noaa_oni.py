"""Recolector del índice ONI (Oceanic Niño Index) de NOAA CPC.

Formato verificado (2026-11-04): texto plano con columnas `SEAS YR TOTAL ANOM`,
p. ej. `ASO 2026  29.23   2.46`. Se descarga el archivo COMPLETO cada vez porque
NOAA revisa valores históricos cuando actualiza su climatología base.
"""

from pathlib import Path

import requests

from agents.comun.archivos import ahora_utc, guardar_crudo
from agents.comun.http import TIMEOUT_S, crear_sesion
from agents.comun.resultado import Resultado
from agents.comun.rutas import RAW

URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
RUTA_CRUDO = RAW / "noaa" / "oni.ascii.txt"


def ejecutar(destino: Path = RUTA_CRUDO, sesion: requests.Session | None = None) -> Resultado:
    sesion = sesion or crear_sesion()
    respuesta = sesion.get(URL_ONI, timeout=TIMEOUT_S)
    respuesta.raise_for_status()

    # Validación mínima: si NOAA cambia el formato, mejor fallar aquí que analizar basura.
    primera_linea = respuesta.text.lstrip().splitlines()[0].split()
    if primera_linea != ["SEAS", "YR", "TOTAL", "ANOM"]:
        raise ValueError(f"Encabezado inesperado en ONI: {primera_linea}")

    guardar_crudo(
        destino,
        respuesta.content,
        {
            "fuente": "NOAA Climate Prediction Center — Oceanic Niño Index (ONI)",
            "url": URL_ONI,
            "descargado_en": ahora_utc(),
        },
    )
    n_filas = len(respuesta.text.strip().splitlines()) - 1
    return Resultado("recolector.noaa_oni", f"ONI: {n_filas} trimestres descargados", [destino])
