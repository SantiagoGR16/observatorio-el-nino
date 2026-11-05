"""Pruebas del recolector con una sesión HTTP falsa (sin internet)."""

import json

import pytest

from agents.recolector import noaa_oni


class RespuestaFalsa:
    def __init__(self, texto: str):
        self.text = texto
        self.content = texto.encode()

    def raise_for_status(self) -> None:
        pass


class SesionFalsa:
    def __init__(self, texto: str):
        self.texto = texto

    def get(self, url, timeout):
        return RespuestaFalsa(self.texto)


def test_oni_guarda_crudo_y_metadatos(tmp_path):
    destino = tmp_path / "oni.ascii.txt"
    texto = " SEAS  YR   TOTAL   ANOM\n  DJF 1950  25.01  -1.32\n"
    r = noaa_oni.ejecutar(destino, SesionFalsa(texto))
    assert destino.read_text() == texto
    meta = json.loads((tmp_path / "oni.ascii.txt.meta.json").read_text(encoding="utf-8"))
    assert meta["url"] == noaa_oni.URL_ONI and meta["descargado_en"].endswith("Z")
    assert "1 trimestres" in r.resumen


def test_oni_falla_si_cambia_el_formato(tmp_path):
    with pytest.raises(ValueError, match="Encabezado inesperado"):
        noaa_oni.ejecutar(tmp_path / "x.txt", SesionFalsa("<html>Mantenimiento</html>"))
