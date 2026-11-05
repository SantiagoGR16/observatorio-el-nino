# Observatorio agéntico de El Niño 2026–2027

## Qué es este proyecto
Sistema multiagente que cada semana recoge datos sobre el fenómeno de El Niño en Colombia,
cruza clima con impactos por municipio, calcula un índice de riesgo territorial y publica
un boletín y un dashboard web. Es un proyecto de portafolio de un analista de datos
(Python, SQL) que además está aprendiendo Angular: explica las decisiones de Angular
cuando las tomes y deja el código comentado en español.

## Arquitectura
- `agents/` — Python 3.11+. Pipeline de agentes con el Claude Agent SDK (o la API de
  Claude con tool use). Cada agente es un módulo con responsabilidad única:
  1. `recolector`: descarga datos de las fuentes y los guarda crudos en `data/raw/`.
  2. `analista`: limpia, une por municipio (código DIVIPOLA) y fecha, calcula indicadores
     y compara con eventos previos (2015–16, 2023–24). Salida en `data/processed/`.
  3. `riesgo`: índice de vulnerabilidad municipal (exposición climática + dependencia
     agrícola + capacidad institucional). Salida GeoJSON.
  4. `redactor`: genera el boletín semanal en Markdown/JSON en lenguaje claro.
  5. `verificador`: comprueba que cada cifra del boletín coincida con los datos procesados;
     si algo no cuadra, el pipeline falla y no publica.
- `data/` — JSON/GeoJSON generados. Es la "base de datos" de la v1 (sin servidor).
- `web/` — Angular (standalone components, TypeScript estricto) + Chart.js vía `ng2-charts`
  + Leaflet para el mapa. Lee los JSON de `data/` (copiados a `web/public/data/` en el build).
  Se despliega en Vercel.
- `.github/workflows/pipeline.yml` — GitHub Actions con cron semanal que corre el pipeline,
  hace commit de los datos nuevos y dispara el redespliegue en Vercel.

## Fuentes de datos (verificar URLs y formatos antes de programar contra ellas)
- NOAA CPC: índice ONI y Niño 3.4.
- IDEAM: boletines ENOS, predicción climática, alertas.
- XM: nivel de embalses y precio de bolsa de energía.
- DANE SIPSA: precios mayoristas de alimentos.
- UNGRD: emergencias reportadas por municipio.
- DNP TerriData: variables municipales para vulnerabilidad.
- datos.gov.co (API Socrata) cuando haya dataset disponible.

## Fases
1. Esqueleto del repo + `recolector` y `analista` con ONI y embalses → JSON en `data/`.
2. App Angular con layout, gráficas Chart.js (ONI, embalses) y mapa Leaflet; deploy en Vercel.
3. Agentes `riesgo`, `redactor` y `verificador`; boletín semanal en el sitio; GitHub Actions.
4. Chat con un agente que responde preguntas sobre los datos (ruta serverless en Vercel).

Trabajar una fase a la vez. No avanzar a la siguiente sin que la actual funcione de punta a punta.

## Convenciones
- Python: `uv` o `venv` + `requirements.txt`, type hints, `ruff`. Tests con `pytest`.
- Secretos (ANTHROPIC_API_KEY, etc.) solo en `.env` (en `.gitignore`) y en GitHub Secrets.
- Toda cifra mostrada en el sitio debe poder rastrearse a su fuente (guardar fuente y fecha
  de descarga en los metadatos de cada JSON).
- Commits pequeños y descriptivos en español.
- README en español con diagrama de arquitectura y cómo correr el proyecto.

## REGLA OBLIGATORIA DE SEGURIDAD — API KEYS
Orden del dueño del proyecto: **nunca dejar una API key ni ningún secreto accesible a terceros.**
- Las claves van solo en `.env` (incluido en `.gitignore` desde el primer commit), en GitHub Secrets
  o en variables de entorno del servidor en Vercel.
- Nunca escribirlas en el código, en el frontend de Angular, en commits, logs, README, issues
  ni en archivos de ejemplo (usar `.env.example` con valores vacíos).
- Antes de cada commit, verificar que ningún archivo contiene una clave.
- Si se detecta una clave expuesta, detenerse y avisar de inmediato para revocarla.
