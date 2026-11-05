// Copia los JSON generados por el pipeline de Python (../data/processed/) a
// web/public/data/, desde donde Angular los sirve como archivos estáticos.
// Se ejecuta solo antes de `npm start` y `npm run build` (scripts "pre*" de npm).
// Falla si falta algún archivo: mejor no compilar que publicar un sitio sin datos.
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const raizWeb = join(dirname(fileURLToPath(import.meta.url)), '..');
const origen = join(raizWeb, '..', 'data', 'processed');
const destino = join(raizWeb, 'public', 'data');
const archivos = ['oni.json', 'embalses.json', 'departamentos.geojson'];

mkdirSync(destino, { recursive: true });
for (const archivo of archivos) {
  const ruta = join(origen, archivo);
  if (!existsSync(ruta)) {
    console.error(`✖ Falta ${ruta}. Corre primero el pipeline: python -m agents.pipeline`);
    process.exit(1);
  }
  copyFileSync(ruta, join(destino, archivo));
  console.log(`✔ data/processed/${archivo} → public/data/${archivo}`);
}
