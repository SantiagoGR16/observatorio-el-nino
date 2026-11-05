"""Recolector de niveles de embalses de XM (API pública servapibi.xm.com.co).

Hechos verificados contra la API (2026-11-04):
- Consulta con POST JSON a /daily: {"MetricId", "Entity", "StartDate", "EndDate", "Filter"}.
- Máximo 31 días por consulta (si no, HTTP 400). Por eso se descarga mes a mes.
- Hay histórico al menos desde 2015. Los datos llegan con 1–2 días de rezago.
- /lists con MetricId "ListadoEmbalses" da cada embalse con su región hidrológica.

Estrategia: un archivo crudo por (métrica, entidad, mes) en data/raw/xm/.
Los meses viejos ya descargados no se vuelven a pedir; los recientes sí, porque XM
puede corregir datos de días anteriores y el mes en curso está incompleto.
"""

import calendar
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import requests

from agents.comun.archivos import ahora_utc, guardar_crudo
from agents.comun.http import TIMEOUT_S, crear_sesion
from agents.comun.resultado import Resultado
from agents.comun.rutas import RAW

URL_DAILY = "https://servapibi.xm.com.co/daily"
URL_LISTS = "https://servapibi.xm.com.co/lists"
FUENTE = "XM S.A. E.S.P. — API pública de datos del mercado (servapibi)"

# (MetricId, Entity) que necesita el analista:
# - % oficial del sistema (la cifra que publica XM).
# - Volumen y capacidad útil en energía por embalse, para calcular % por región
#   ponderado por capacidad (sumar kWh, no promediar porcentajes).
METRICAS: list[tuple[str, str]] = [
    ("PorcVoluUtilDiar", "Sistema"),
    ("VoluUtilDiarEner", "Embalse"),
    ("CapaUtilDiarEner", "Embalse"),
]
INICIO_HISTORICO = date(2015, 1, 1)  # cubre El Niño 2015–16 y 2023–24
DIAS_A_REFRESCAR = 45  # meses que tocan esta ventana se vuelven a descargar siempre

DIR_XM = RAW / "xm"


def meses(desde: date, hasta: date) -> Iterator[tuple[date, date]]:
    """Genera (primer_dia, ultimo_dia) de cada mes entre dos fechas, recortando los bordes.

    Cada tramo tiene como mucho 31 días, así que respeta el límite de la API.
    """
    actual = desde.replace(day=1)
    while actual <= hasta:
        ultimo = actual.replace(day=calendar.monthrange(actual.year, actual.month)[1])
        yield max(actual, desde), min(ultimo, hasta)
        actual = ultimo + timedelta(days=1)


def ruta_mes(metrica: str, entidad: str, inicio_mes: date, base: Path = DIR_XM) -> Path:
    return base / f"{metrica}_{entidad}" / f"{inicio_mes:%Y-%m}.json"


def consultar_daily(
    sesion: requests.Session, metrica: str, entidad: str, inicio: date, fin: date
) -> tuple[bytes, dict]:
    cuerpo = {
        "MetricId": metrica,
        "Entity": entidad,
        "StartDate": inicio.isoformat(),
        "EndDate": fin.isoformat(),
        "Filter": [],
    }
    respuesta = sesion.post(URL_DAILY, json=cuerpo, timeout=TIMEOUT_S)
    respuesta.raise_for_status()
    if "Items" not in respuesta.json():
        raise ValueError(f"Respuesta de XM sin 'Items' para {metrica}/{entidad} {inicio}")
    return respuesta.content, cuerpo


def ejecutar(
    hoy: date | None = None,
    base: Path = DIR_XM,
    sesion: requests.Session | None = None,
) -> Resultado:
    hoy = hoy or date.today()
    sesion = sesion or crear_sesion()
    limite_refresco = hoy - timedelta(days=DIAS_A_REFRESCAR)
    archivos: list[Path] = []
    descargados = reutilizados = 0

    # 1) Catálogo de embalses con su región (cambia poco, pero es barato pedirlo siempre).
    cuerpo_lista = {"MetricId": "ListadoEmbalses", "Entity": "Sistema"}
    resp = sesion.post(URL_LISTS, json=cuerpo_lista, timeout=TIMEOUT_S)
    resp.raise_for_status()
    ruta_lista = base / "ListadoEmbalses.json"
    guardar_crudo(
        ruta_lista,
        resp.content,
        {
            "fuente": FUENTE,
            "url": URL_LISTS,
            "parametros": cuerpo_lista,
            "descargado_en": ahora_utc(),
        },
    )
    archivos.append(ruta_lista)

    # 2) Series diarias, mes a mes.
    for metrica, entidad in METRICAS:
        for inicio, fin in meses(INICIO_HISTORICO, hoy):
            ruta = ruta_mes(metrica, entidad, inicio, base)
            mes_reciente = fin >= limite_refresco
            if ruta.exists() and not mes_reciente:
                reutilizados += 1
                archivos.append(ruta)
                continue
            contenido, cuerpo = consultar_daily(sesion, metrica, entidad, inicio, fin)
            guardar_crudo(
                ruta,
                contenido,
                {
                    "fuente": FUENTE,
                    "url": URL_DAILY,
                    "parametros": cuerpo,
                    "descargado_en": ahora_utc(),
                },
            )
            descargados += 1
            archivos.append(ruta)

    resumen = (
        f"XM: {descargados} consultas nuevas, {reutilizados} meses ya en caché "
        f"({len(METRICAS)} métricas desde {INICIO_HISTORICO:%Y-%m})"
    )
    return Resultado("recolector.xm_embalses", resumen, archivos)


if __name__ == "__main__":  # permite probarlo solo: python -m agents.recolector.xm_embalses
    print(ejecutar().resumen)
