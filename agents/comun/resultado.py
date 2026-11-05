"""Contrato común de los agentes: cada `ejecutar()` devuelve un `Resultado`."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Resultado:
    agente: str  # p. ej. "recolector.noaa_oni"
    resumen: str  # una línea legible para el log del pipeline
    archivos: list[Path] = field(default_factory=list)  # lo que produjo
