"""Lectura/escritura de archivos con metadatos de trazabilidad.

Regla del proyecto: toda cifra publicada debe poder rastrearse a su fuente. Por eso
cada archivo crudo tiene un `<nombre>.meta.json` al lado y cada JSON procesado lleva
un bloque `metadatos` con fuente, URL y fecha de descarga.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def ahora_utc() -> str:
    """Marca de tiempo ISO 8601 en UTC, p. ej. '2026-11-04T15:20:00Z'."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def escribir_json(ruta: Path, datos: Any, compacto: bool = False) -> Path:
    """Escribe JSON en UTF-8 de forma atómica (archivo temporal + renombrar).

    Si el proceso se corta a mitad de escritura, el archivo anterior queda intacto
    en vez de quedar un JSON corrupto a medias. `compacto=True` omite espacios y
    saltos de línea (útil para GeoJSON, donde la sangría triplica el tamaño).
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    if compacto:
        texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    else:
        texto = json.dumps(datos, ensure_ascii=False, indent=1)
    temporal.write_text(texto, encoding="utf-8")
    temporal.replace(ruta)
    return ruta


def leer_json(ruta: Path) -> Any:
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_crudo(ruta: Path, contenido: bytes, metadatos: dict[str, Any]) -> Path:
    """Guarda el contenido exactamente como llegó y, al lado, su `.meta.json`."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    escribir_json(ruta.with_name(ruta.name + ".meta.json"), metadatos)
    return ruta
