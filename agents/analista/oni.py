"""Analista del ONI: clasifica cada trimestre y detecta eventos El Niño / La Niña.

Regla (NOAA CPC): hay evento cuando la anomalía ONI es >= +0.5 °C (Niño) o <= -0.5 °C
(Niña) durante al menos 5 trimestres móviles consecutivos.

Nota: se usa el valor con 2 decimales del archivo ascii tal cual (sin redondear a 1
decimal como la tabla web de NOAA), así que en casos límite (p. ej. 0.46) podría haber
pequeñas diferencias con esa tabla.
"""

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from agents.comun.archivos import ahora_utc, escribir_json, leer_json
from agents.comun.resultado import Resultado
from agents.comun.rutas import PROCESSED
from agents.recolector.noaa_oni import RUTA_CRUDO

UMBRAL = 0.5
MIN_TRIMESTRES = 5
# Trimestres en orden; el índice + 1 es el mes central (DJF -> enero, NDJ -> diciembre).
TRIMESTRES = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
# Escala de intensidad por pico (convención común, NO oficial de NOAA).
INTENSIDADES = [(2.0, "muy fuerte"), (1.5, "fuerte"), (1.0, "moderado"), (0.5, "débil")]
# Eventos El Niño de referencia: (año cuyo trimestre se compara con el actual, etiqueta).
EVENTOS_REFERENCIA = [(1997, "1997–98"), (2015, "2015–16"), (2023, "2023–24")]

RUTA_SALIDA = PROCESSED / "oni.json"


def parsear(texto: str) -> pd.DataFrame:
    """Convierte el ascii de NOAA en un DataFrame ordenado cronológicamente."""
    df = pd.read_csv(StringIO(texto), sep=r"\s+")
    df = df.rename(
        columns={"SEAS": "trimestre", "YR": "anio", "TOTAL": "total", "ANOM": "anomalia"}
    )
    desconocidos = set(df["trimestre"]) - set(TRIMESTRES)
    if desconocidos:
        raise ValueError(f"Trimestres desconocidos en ONI: {desconocidos}")
    df["mes_central"] = df["trimestre"].map(TRIMESTRES.index) + 1
    df["fecha"] = pd.to_datetime(
        {"year": df["anio"], "month": df["mes_central"], "day": 1}
    ).dt.strftime("%Y-%m")
    return df.sort_values("fecha", ignore_index=True)


def intensidad(pico: float) -> str:
    for umbral, nombre in INTENSIDADES:
        if abs(pico) >= umbral:
            return nombre
    return "neutral"


def detectar_eventos(df: pd.DataFrame) -> tuple[pd.Series, list[dict[str, Any]]]:
    """Devuelve la fase de cada trimestre y la lista de eventos.

    Agrupa rachas consecutivas con el mismo signo por encima del umbral. Una racha
    que llega al último dato y aún no suma 5 trimestres se marca "en formación".
    """
    signo = pd.Series(0, index=df.index)
    signo[df["anomalia"] >= UMBRAL] = 1
    signo[df["anomalia"] <= -UMBRAL] = -1
    # Truco clásico de pandas: cada cambio de valor abre un nuevo grupo de racha.
    racha_id = (signo != signo.shift()).cumsum()

    fase = pd.Series("Neutral", index=df.index)
    eventos: list[dict[str, Any]] = []
    ultimo_idx = df.index[-1]
    for _, idx in signo.groupby(racha_id).groups.items():
        s = signo[idx[0]]
        if s == 0:
            continue
        tipo = "El Niño" if s == 1 else "La Niña"
        tramo = df.loc[idx]
        en_curso = idx[-1] == ultimo_idx
        if len(idx) < MIN_TRIMESTRES and not en_curso:
            continue  # racha corta ya terminada: no es evento
        i_pico = tramo["anomalia"].abs().idxmax()
        estado = (
            "en formación"
            if len(idx) < MIN_TRIMESTRES
            else ("en curso" if en_curso else "terminado")
        )
        if estado != "en formación":
            fase[idx] = tipo
        eventos.append(
            {
                "tipo": tipo,
                "estado": estado,
                "inicio": f"{tramo['trimestre'].iloc[0]} {tramo['anio'].iloc[0]}",
                "fin": f"{tramo['trimestre'].iloc[-1]} {tramo['anio'].iloc[-1]}",
                "fecha_inicio": tramo["fecha"].iloc[0],
                "fecha_fin": tramo["fecha"].iloc[-1],
                "duracion_trimestres": len(idx),
                "pico": float(df.at[i_pico, "anomalia"]),
                "trimestre_pico": f"{df.at[i_pico, 'trimestre']} {df.at[i_pico, 'anio']}",
                "intensidad": intensidad(df.at[i_pico, "anomalia"]),
            }
        )
    return fase, eventos


def comparar(df: pd.DataFrame, eventos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compara el último trimestre con el mismo trimestre de los eventos de referencia."""
    ultimo = df.iloc[-1]
    ninos = [e for e in eventos if e["tipo"] == "El Niño"]
    filas = []
    for anio, etiqueta in EVENTOS_REFERENCIA:
        mismo = df[(df["anio"] == anio) & (df["trimestre"] == ultimo["trimestre"])]
        # Buscamos el evento que CONTIENE ese trimestre (no el que empieza ese año):
        # p. ej. El Niño 2015–16 arranca en SON 2014 según la serie actual de NOAA.
        fecha = mismo["fecha"].iloc[0] if len(mismo) else ""
        evento = next((e for e in ninos if e["fecha_inicio"] <= fecha <= e["fecha_fin"]), None)
        filas.append(
            {
                "evento": etiqueta,
                "trimestre_comparado": f"{ultimo['trimestre']} {anio}",
                "anomalia_mismo_trimestre": float(mismo["anomalia"].iloc[0])
                if len(mismo)
                else None,
                "pico": evento["pico"] if evento else None,
                "trimestre_pico": evento["trimestre_pico"] if evento else None,
                "duracion_trimestres": evento["duracion_trimestres"] if evento else None,
            }
        )
    return filas


def ejecutar(origen: Path = RUTA_CRUDO, destino: Path = RUTA_SALIDA) -> Resultado:
    meta_crudo = leer_json(origen.with_name(origen.name + ".meta.json"))
    df = parsear(origen.read_text(encoding="utf-8"))
    df["fase"], eventos = detectar_eventos(df)
    ultimo = df.iloc[-1]
    evento_actual = eventos[-1] if eventos and eventos[-1]["estado"] != "terminado" else None

    salida = {
        "metadatos": {
            **meta_crudo,  # fuente, url, descargado_en
            "procesado_en": ahora_utc(),
            "unidad": "°C (anomalía de temperatura superficial del mar, región Niño 3.4)",
            "metodologia": (
                f"Evento si la anomalía es >= +{UMBRAL} (Niño) o <= -{UMBRAL} (Niña) por "
                f"{MIN_TRIMESTRES}+ trimestres móviles consecutivos (criterio NOAA CPC). "
                "Intensidad por pico: débil 0.5–0.9, moderado 1.0–1.4, fuerte 1.5–1.9, "
                "muy fuerte >= 2.0 (convención común, no oficial de NOAA)."
            ),
        },
        "ultimo": {
            "trimestre": f"{ultimo['trimestre']} {ultimo['anio']}",
            "fecha": ultimo["fecha"],
            "anomalia": float(ultimo["anomalia"]),
            "fase": ultimo["fase"],
            "evento_actual": evento_actual,
        },
        "comparacion_eventos": comparar(df, eventos),
        "eventos": eventos,
        "serie": [
            {
                "trimestre": r.trimestre,
                "anio": int(r.anio),
                "fecha": r.fecha,
                "total": float(r.total),
                "anomalia": float(r.anomalia),
                "fase": r.fase,
            }
            for r in df.itertuples()
        ],
    }
    escribir_json(destino, salida)
    resumen = (
        f"ONI {salida['ultimo']['trimestre']}: {ultimo['anomalia']:+.2f} °C "
        f"({ultimo['fase']}); {len(eventos)} eventos detectados"
    )
    return Resultado("analista.oni", resumen, [destino])
