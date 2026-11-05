"""Rutas del proyecto en un solo lugar, para no repetir cadenas por todo el código."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATA = RAIZ / "data"
RAW = DATA / "raw"  # datos crudos tal como llegan de la fuente (no se versionan)
PROCESSED = DATA / "processed"  # datos limpios que consume la web (sí se versionan)
