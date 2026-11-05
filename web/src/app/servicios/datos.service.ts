// Servicio de datos: el ÚNICO lugar de la app que sabe dónde están los JSON.
// Los componentes no hacen peticiones HTTP; le piden los datos a este servicio.
// Así, si en el futuro los datos vienen de una API en vez de archivos, solo cambia esto.
import { httpResource } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { DatosEmbalses, DatosOni, Departamentos } from '../modelos/datos';

// Ruta relativa: los JSON se copian a web/public/data/ antes de compilar
// (script scripts/copiar-datos.mjs) y se sirven como archivos estáticos.
const BASE = 'data';

// `providedIn: 'root'` = una sola instancia para toda la app (singleton).
@Injectable({ providedIn: 'root' })
export class DatosService {
  // httpResource crea un "recurso" basado en signals: hace la petición y expone
  // .value(), .isLoading(), .error() y .hasValue() como signals que la plantilla
  // puede leer directamente. Se dispara al crear el servicio (primera inyección).
  readonly oni = httpResource<DatosOni>(() => `${BASE}/oni.json`);
  readonly embalses = httpResource<DatosEmbalses>(() => `${BASE}/embalses.json`);
  readonly departamentos = httpResource<Departamentos>(() => `${BASE}/departamentos.geojson`);
}
