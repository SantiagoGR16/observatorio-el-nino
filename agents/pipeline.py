"""Orquestador del pipeline (fase 1): recolector -> analista.

Uso:
    python -m agents.pipeline              # descarga + análisis
    python -m agents.pipeline --sin-descarga   # solo re-analiza lo que hay en data/raw/

Si cualquier agente falla, se lanza la excepción y el proceso termina con código != 0;
así GitHub Actions (fase 3) marcará la corrida como fallida y no publicará nada.
"""

import argparse
import logging
from collections.abc import Callable

from agents.analista import departamentos as analista_departamentos
from agents.analista import embalses as analista_embalses
from agents.analista import oni as analista_oni
from agents.comun.resultado import Resultado
from agents.recolector import dane_departamentos, noaa_oni, xm_embalses

log = logging.getLogger("pipeline")

RECOLECTORES: list[Callable[[], Resultado]] = [
    noaa_oni.ejecutar,
    xm_embalses.ejecutar,
    dane_departamentos.ejecutar,
]
ANALISTAS: list[Callable[[], Resultado]] = [
    analista_oni.ejecutar,
    analista_embalses.ejecutar,
    analista_departamentos.ejecutar,
]


def correr(descargar: bool = True) -> list[Resultado]:
    pasos = (RECOLECTORES if descargar else []) + ANALISTAS
    resultados = []
    for paso in pasos:
        resultado = paso()
        log.info("✔ %-24s %s", resultado.agente, resultado.resumen)
        resultados.append(resultado)
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline del Observatorio de El Niño")
    parser.add_argument(
        "--sin-descarga",
        action="store_true",
        help="no descarga; solo analiza los datos crudos existentes",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    correr(descargar=not args.sin_descarga)


if __name__ == "__main__":
    main()
