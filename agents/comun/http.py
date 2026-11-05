"""Cliente HTTP compartido con reintentos automáticos.

Las APIs públicas a veces responden 429/5xx de forma pasajera. En lugar de que el
pipeline semanal falle por eso, reintentamos con espera exponencial (1 s, 2 s, 4 s...).
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Identificador genérico del cliente (sin datos personales).
USER_AGENT = "observatorio-nino-colombia/0.1 (+proyecto de portafolio)"
TIMEOUT_S = 60


def crear_sesion() -> requests.Session:
    """Devuelve una sesión que reintenta GET y POST ante errores transitorios."""
    reintentos = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),  # XM usa POST para consultar (es idempotente)
    )
    sesion = requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT
    sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
    return sesion
