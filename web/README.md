# web/ — Dashboard en Angular

App Angular 22 (standalone, zoneless, signals) que lee los JSON de `../data/processed/`.

```powershell
npm install
npm start          # copia los datos y abre http://localhost:4200
npm run build      # copia los datos y compila a dist/web/browser
npx ng test --watch=false   # pruebas con Vitest
```

`npm start` y `npm run build` ejecutan antes `scripts/copiar-datos.mjs`, que copia
`data/processed/*` a `public/data/` (carpeta ignorada por git). Si faltan los datos,
corre primero el pipeline de Python desde la raíz: `python -m agents.pipeline`.

## Estructura

| Carpeta | Qué contiene |
|---|---|
| `src/app/modelos/` | Interfaces TypeScript de los JSON del pipeline |
| `src/app/servicios/` | `DatosService`: único lugar que hace peticiones HTTP (`httpResource`) |
| `src/app/componentes/` | Piezas reutilizables: tarjetas, gráficas Chart.js, mapa Leaflet, pie de fuente |
| `src/app/paginas/` | Páginas enrutadas (por ahora, el dashboard, cargado en diferido) |
| `src/app/utilidades/` | Funciones puras (ejes, colores) con pruebas Vitest |

## Decisiones

- **Chart.js se registra en el componente Dashboard**, no en `app.config.ts`, para que
  viaje en el paquete diferido: la carga inicial bajó de 499 kB a 291 kB.
- **Mapa base de OpenStreetMap** (sin API key). Nunca se pone una clave en el frontend.
- **Límites departamentales del DANE** simplificados a ~1 km: aptos para visualizar,
  no para calcular áreas.
