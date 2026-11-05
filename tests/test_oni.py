"""Pruebas del analista ONI. Usan una copia real del archivo de NOAA (sin internet)."""

from pathlib import Path

import pandas as pd
import pytest

from agents.analista import oni

FIXTURE = Path(__file__).parent / "fixtures" / "oni_2026-11-04.ascii.txt"


@pytest.fixture(scope="module")
def df_real() -> pd.DataFrame:
    return oni.parsear(FIXTURE.read_text(encoding="utf-8"))


def serie(anomalias: list[float]) -> pd.DataFrame:
    """Serie sintética mensual a partir de DJF 2000."""
    filas = []
    for i, a in enumerate(anomalias):
        t = oni.TRIMESTRES[i % 12]
        filas.append(
            {
                "trimestre": t,
                "anio": 2000 + i // 12,
                "total": 27.0,
                "anomalia": a,
                "fecha": f"{2000 + i // 12}-{i % 12 + 1:02d}",
            }
        )
    return pd.DataFrame(filas)


def test_parsear_mes_central(df_real):
    primero = df_real.iloc[0]
    assert (primero["trimestre"], primero["fecha"]) == ("DJF", "1950-01")
    ndj = df_real[df_real["trimestre"] == "NDJ"].iloc[0]
    assert ndj["fecha"] == "1950-12"  # NDJ 1950 = nov 1950–ene 1951, centro diciembre
    assert df_real["fecha"].is_monotonic_increasing


def test_cuatro_trimestres_no_son_evento():
    _, eventos = oni.detectar_eventos(serie([0, 0.6, 0.7, 0.8, 0.6, 0.2, 0]))
    assert eventos == []


def test_cinco_trimestres_si_son_evento():
    fase, eventos = oni.detectar_eventos(serie([0, 0.5, 0.7, 1.6, 0.9, 0.5, 0.1]))
    assert len(eventos) == 1
    e = eventos[0]
    assert (e["tipo"], e["estado"], e["duracion_trimestres"]) == ("El Niño", "terminado", 5)
    assert e["pico"] == 1.6 and e["intensidad"] == "fuerte"
    assert list(fase) == ["Neutral"] + ["El Niño"] * 5 + ["Neutral"]


def test_nina_y_racha_final_en_formacion():
    fase, eventos = oni.detectar_eventos(serie([-0.6, -0.8, -1.1, -0.9, -0.5, 0, 0.6, 0.9]))
    assert [(e["tipo"], e["estado"]) for e in eventos] == [
        ("La Niña", "terminado"),
        ("El Niño", "en formación"),
    ]
    # Una racha "en formación" aún no se marca como fase El Niño.
    assert fase.iloc[-1] == "Neutral"


def test_eventos_historicos_conocidos(df_real):
    _, eventos = oni.detectar_eventos(df_real)
    comparacion = {c["evento"]: c for c in oni.comparar(df_real, eventos)}
    # El Niño 2015–16 empieza en SON 2014 en la serie actual: antes era un bug.
    assert comparacion["2015–16"]["pico"] == 2.59
    assert comparacion["2023–24"]["pico"] == 1.99
    assert eventos[-1]["estado"] == "en curso"


def test_intensidad_escala():
    assert [oni.intensidad(x) for x in (0.3, 0.5, 1.0, 1.5, 2.0, -1.2)] == [
        "neutral",
        "débil",
        "moderado",
        "fuerte",
        "muy fuerte",
        "moderado",
    ]
