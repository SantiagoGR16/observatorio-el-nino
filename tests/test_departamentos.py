"""Pruebas de la unión geometría MGN + nombres DIVIPOLA (sin internet)."""

import pytest

from agents.analista import departamentos

CUADRADO = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}


def mgn(*codigos: str) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            # Nombre dañado tal como llega del servidor: debe ignorarse.
            {
                "type": "Feature",
                "properties": {"DPTO_CCDGO": c, "DPTO_CNMBRE": "BOGOT�"},
                "geometry": CUADRADO,
            }
            for c in codigos
        ],
    }


def test_une_por_codigo_y_usa_nombre_de_divipola():
    divipola = [{"cod_dpto": "11", "dpto": "BOGOTÁ, D.C."}, {"cod_dpto": "05", "dpto": "ANTIOQUIA"}]
    salida = departamentos.unir(mgn("11", "05"), divipola)
    props = [f["properties"] for f in salida["features"]]
    assert props == [
        {"codigo": "05", "nombre": "ANTIOQUIA"},
        {"codigo": "11", "nombre": "BOGOTÁ, D.C."},
    ]


def test_falla_si_un_codigo_no_tiene_nombre():
    with pytest.raises(ValueError, match="99"):
        departamentos.unir(mgn("99"), [{"cod_dpto": "05", "dpto": "ANTIOQUIA"}])
