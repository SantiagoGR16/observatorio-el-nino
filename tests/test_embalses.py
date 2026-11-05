"""Pruebas del recolector y analista de embalses XM (datos sintéticos, sin internet)."""

import json
from datetime import date

import pandas as pd

from agents.analista import embalses
from agents.recolector import xm_embalses


def test_meses_respeta_limite_de_31_dias_y_no_deja_huecos():
    tramos = list(xm_embalses.meses(date(2015, 1, 1), date(2026, 11, 3)))
    assert tramos[0] == (date(2015, 1, 1), date(2015, 1, 31))
    assert tramos[-1] == (date(2026, 11, 1), date(2026, 11, 3))
    assert all((fin - ini).days < 31 for ini, fin in tramos)
    assert all((b[0] - a[1]).days == 1 for a, b in zip(tramos, tramos[1:], strict=False))


def test_leer_metrica_acepta_valor_como_texto_o_numero(tmp_path):
    carpeta = tmp_path / "PorcVoluUtilDiar_Sistema"
    carpeta.mkdir()
    items = [
        {"Date": "2026-11-01", "DailyEntities": [{"Id": "Sistema", "Value": "0.77590"}]},
        {"Date": "2026-11-02", "DailyEntities": [{"Id": "Sistema", "Value": 0.7787}]},
    ]
    (carpeta / "2026-11.json").write_text(json.dumps({"Items": items}), encoding="utf-8")
    (carpeta / "2026-11.json.meta.json").write_text("{}", encoding="utf-8")  # se ignora
    df = embalses.leer_metrica(tmp_path, "PorcVoluUtilDiar", "Sistema")
    assert df["valor"].tolist() == [0.7759, 0.7787]
    assert df["nombre"].tolist() == ["Sistema", "Sistema"]


def test_region_se_pondera_por_capacidad():
    f = pd.Timestamp("2026-11-03")
    volu = pd.DataFrame({"fecha": [f, f], "nombre": ["GRANDE", "PEQUENO"], "valor": [90.0, 1.0]})
    capa = pd.DataFrame({"fecha": [f, f], "nombre": ["GRANDE", "PEQUENO"], "valor": [100.0, 10.0]})
    r = embalses.por_region(volu, capa, {"GRANDE": "X", "PEQUENO": "X"})
    # 91/110 = 82.7 %, NO el promedio simple de 90 % y 10 % (= 50 %).
    assert round(r["porcentaje"].iloc[0], 1) == 82.7
    assert r["n_embalses"].iloc[0] == 2


def test_embalse_desconocido_va_a_sin_region():
    f = pd.Timestamp("2026-11-03")
    df = pd.DataFrame({"fecha": [f], "nombre": ["NUEVO"], "valor": [1.0]})
    r = embalses.por_region(df, df, {})
    assert r["region"].iloc[0] == embalses.SIN_REGION


def test_comparar_temporadas_alinea_desde_1_de_julio():
    fechas = pd.date_range("2015-07-01", "2026-11-03", freq="D")
    # Porcentaje = año, para saber de qué temporada salió cada valor.
    sistema = pd.DataFrame({"fecha": fechas, "porcentaje": fechas.year.astype(float)})
    c = embalses.comparar_temporadas(sistema, date(2026, 11, 3))
    assert c["dia_actual"] == 125
    assert [m["fecha"] for m in c["misma_altura"]] == ["2015-11-03", "2023-11-03", "2026-11-03"]
    assert [t["temporada"] for t in c["temporadas"]] == ["2015–16", "2023–24", "2026–27"]
    assert c["temporadas"][-1]["es_actual"]


def test_inicio_temporada():
    assert embalses.inicio_temporada(date(2027, 3, 15)) == date(2026, 7, 1)
    assert embalses.inicio_temporada(date(2026, 7, 1)) == date(2026, 7, 1)
