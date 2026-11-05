"""Analista de embalses: nivel del sistema, nivel por región y comparación con
El Niño 2015–16 y 2023–24.

Decisiones:
- El % del sistema es la cifra OFICIAL de XM (PorcVoluUtilDiar / Sistema).
- El % por región se calcula como suma(volumen útil kWh) / suma(capacidad útil kWh):
  así cada embalse pesa según su tamaño (promediar porcentajes sería un error).
- Las temporadas se alinean desde el 1 de julio, cuando suele arrancar El Niño;
  el periodo crítico (embalses más bajos) suele ser febrero–abril del año siguiente.
"""

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from agents.comun.archivos import ahora_utc, escribir_json, leer_json
from agents.comun.resultado import Resultado
from agents.comun.rutas import PROCESSED
from agents.recolector.xm_embalses import DIR_XM, FUENTE, METRICAS, URL_DAILY

# Temporadas El Niño a comparar: año en que empiezan (1 de julio).
TEMPORADAS_PREVIAS = [2015, 2023]
DIAS_SERIE_REGIONES = 365
SIN_REGION = "SIN REGIÓN"

RUTA_SALIDA = PROCESSED / "embalses.json"


def leer_metrica(base: Path, metrica: str, entidad: str) -> pd.DataFrame:
    """Une todos los archivos mensuales de una métrica en un DataFrame largo.

    Columnas: fecha (datetime), nombre (embalse o "Sistema"), valor (float).
    """
    filas = []
    for archivo in sorted((base / f"{metrica}_{entidad}").glob("*.json")):
        if archivo.name.endswith(".meta.json"):
            continue
        for item in leer_json(archivo)["Items"]:
            for ent in item["DailyEntities"]:
                filas.append(
                    {
                        "fecha": item["Date"],
                        "nombre": ent.get("Name", ent["Id"]),
                        # XM manda el valor como texto en "Sistema" y como número en
                        # "Embalse": to_numeric (abajo) unifica ambos casos.
                        "valor": ent.get("Value"),
                    }
                )
    df = pd.DataFrame(filas, columns=["fecha", "nombre", "valor"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df


def leer_regiones(base: Path) -> dict[str, str]:
    """Mapa nombre_embalse -> región hidrológica, desde ListadoEmbalses."""
    datos = leer_json(base / "ListadoEmbalses.json")
    return {
        e["Values"]["Name"]: e["Values"]["HydroRegion"]
        for item in datos["Items"]
        for e in item["ListEntities"]
    }


def metadatos_crudos(base: Path) -> dict[str, str]:
    """Rango de fechas de descarga de los archivos crudos usados (trazabilidad)."""
    fechas = [leer_json(p)["descargado_en"] for p in base.rglob("*.meta.json")]
    return {"descarga_mas_antigua": min(fechas), "descarga_mas_reciente": max(fechas)}


def por_region(volu: pd.DataFrame, capa: pd.DataFrame, regiones: dict[str, str]) -> pd.DataFrame:
    """% útil por región y fecha, ponderado por capacidad."""
    df = volu.merge(capa, on=["fecha", "nombre"], suffixes=("_volu", "_capa"))
    df["region"] = df["nombre"].map(lambda nombre: regiones.get(nombre, SIN_REGION))
    g = df.groupby(["fecha", "region"], as_index=False).agg(
        volumen_kwh=("valor_volu", "sum"),
        capacidad_kwh=("valor_capa", "sum"),
        n_embalses=("nombre", "nunique"),
    )
    g["porcentaje"] = 100 * g["volumen_kwh"] / g["capacidad_kwh"]
    return g


def inicio_temporada(d: date) -> date:
    """1 de julio de la temporada a la que pertenece la fecha."""
    return date(d.year if d.month >= 7 else d.year - 1, 7, 1)


def comparar_temporadas(sistema: pd.DataFrame, ultima: date) -> dict[str, Any]:
    """Series alineadas por 'día de temporada' y valor a la misma altura del año."""
    actual = inicio_temporada(ultima).year
    dia_actual = (ultima - date(actual, 7, 1)).days
    temporadas, misma_altura = [], []
    for anio in [*TEMPORADAS_PREVIAS, actual]:
        ini = pd.Timestamp(anio, 7, 1)
        tramo = sistema[
            (sistema["fecha"] >= ini) & (sistema["fecha"] < ini + pd.DateOffset(years=1))
        ]
        etiqueta = f"{anio}–{str(anio + 1)[-2:]}"
        temporadas.append(
            {
                "temporada": etiqueta,
                "es_actual": anio == actual,
                "serie": [
                    {"dia": (f - ini).days, "fecha": f"{f:%Y-%m-%d}", "porcentaje": round(p, 2)}
                    for f, p in zip(tramo["fecha"], tramo["porcentaje"], strict=True)
                ],
                "minimo": (
                    {
                        "fecha": f"{tramo.loc[tramo['porcentaje'].idxmin(), 'fecha']:%Y-%m-%d}",
                        "porcentaje": round(tramo["porcentaje"].min(), 2),
                    }
                    if len(tramo)
                    else None
                ),
            }
        )
        fila = tramo[(tramo["fecha"] - ini).dt.days == dia_actual]
        misma_altura.append(
            {
                "temporada": etiqueta,
                "fecha": f"{fila['fecha'].iloc[0]:%Y-%m-%d}" if len(fila) else None,
                "porcentaje": round(float(fila["porcentaje"].iloc[0]), 2) if len(fila) else None,
            }
        )
    return {
        "descripcion": "Temporadas alineadas desde el 1 de julio; 'dia' = días desde esa fecha.",
        "dia_actual": dia_actual,
        "misma_altura": misma_altura,
        "temporadas": temporadas,
    }


def ejecutar(base: Path = DIR_XM, destino: Path = RUTA_SALIDA) -> Resultado:
    (m_porc, e_porc), (m_volu, e_volu), (m_capa, e_capa) = METRICAS

    # 1) Sistema (cifra oficial, viene como fracción 0–1 -> la pasamos a %).
    sistema = leer_metrica(base, m_porc, e_porc).dropna(subset=["valor"])
    sistema = sistema.assign(porcentaje=sistema["valor"] * 100)[["fecha", "porcentaje"]]
    sistema = sistema.sort_values("fecha", ignore_index=True)

    # 2) Regiones (ponderado por capacidad).
    volu = leer_metrica(base, m_volu, e_volu)
    capa = leer_metrica(base, m_capa, e_capa)
    nulos = int(volu["valor"].isna().sum() + capa["valor"].isna().sum())
    regiones_map = leer_regiones(base)
    regiones = por_region(volu.dropna(), capa.dropna(), regiones_map)

    ultima_ts = sistema["fecha"].max()
    ultima = ultima_ts.date()

    def valor_hace(dias: int) -> float | None:
        fila = sistema[sistema["fecha"] == ultima_ts - pd.Timedelta(days=dias)]
        return float(fila["porcentaje"].iloc[0]) if len(fila) else None

    actual_pct = float(sistema["porcentaje"].iloc[-1])
    variaciones = {}
    for dias in (7, 30):
        previo = valor_hace(dias)
        variaciones[f"variacion_{dias}d_pp"] = (
            round(actual_pct - previo, 2) if previo is not None else None
        )

    # 3) Control de calidad: % del sistema reconstruido desde embalses vs. oficial.
    total = regiones.groupby("fecha")[["volumen_kwh", "capacidad_kwh"]].sum()
    reconstruido = (100 * total["volumen_kwh"] / total["capacidad_kwh"]).rename("reconstruido")
    cruce = sistema.set_index("fecha").join(reconstruido, how="inner")
    diferencia = (cruce["porcentaje"] - cruce["reconstruido"]).abs()
    sin_region = sorted(set(volu["nombre"]) - set(regiones_map))

    ult_reg = regiones[regiones["fecha"] == ultima_ts].sort_values("porcentaje")
    desde = ultima_ts - pd.Timedelta(days=DIAS_SERIE_REGIONES)
    reciente = regiones[regiones["fecha"] > desde]

    salida = {
        "metadatos": {
            "fuente": FUENTE,
            "url": URL_DAILY,
            "metricas": [f"{m}/{e}" for m, e in METRICAS] + ["ListadoEmbalses"],
            **metadatos_crudos(base),
            "procesado_en": ahora_utc(),
            "unidad": "% del volumen útil (energía almacenada / capacidad útil)",
            "metodologia": (
                "Sistema: cifra oficial de XM (PorcVoluUtilDiar). Regiones: suma de volumen "
                "útil en kWh / suma de capacidad útil en kWh de sus embalses (ponderado por "
                "capacidad). Temporadas comparadas desde el 1 de julio."
            ),
        },
        "ultimo": {
            "fecha": f"{ultima:%Y-%m-%d}",
            "porcentaje_sistema": round(actual_pct, 2),
            **variaciones,
        },
        "regiones_ultimo": [
            {
                "region": r.region,
                "porcentaje": round(r.porcentaje, 2),
                "volumen_util_gwh": round(r.volumen_kwh / 1e6, 1),
                "capacidad_util_gwh": round(r.capacidad_kwh / 1e6, 1),
                "n_embalses": int(r.n_embalses),
            }
            for r in ult_reg.itertuples()
        ],
        "comparacion_temporadas": comparar_temporadas(sistema, ultima),
        "serie_sistema": [
            {"fecha": f"{f:%Y-%m-%d}", "porcentaje": round(p, 2)}
            for f, p in zip(sistema["fecha"], sistema["porcentaje"], strict=True)
        ],
        "serie_regiones": [
            {
                "region": reg,
                "serie": [
                    {"fecha": f"{f:%Y-%m-%d}", "porcentaje": round(p, 2)}
                    for f, p in zip(g["fecha"], g["porcentaje"], strict=True)
                ],
            }
            for reg, g in reciente.groupby("region")
        ],
        "control_calidad": {
            "dias_sistema": len(sistema),
            "valores_nulos_descartados": nulos,
            "embalses_sin_region": sin_region,
            "diferencia_max_pp_oficial_vs_reconstruido": round(float(diferencia.max()), 3),
            "diferencia_media_pp_oficial_vs_reconstruido": round(float(diferencia.mean()), 3),
        },
    }
    escribir_json(destino, salida)
    u = salida["ultimo"]
    resumen = (
        f"Embalses {u['fecha']}: {u['porcentaje_sistema']:.1f} % "
        f"(7 d: {u['variacion_7d_pp']:+.2f} pp); {len(ult_reg)} regiones"
    )
    return Resultado("analista.embalses", resumen, [destino])
