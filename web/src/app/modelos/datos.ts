// Interfaces que describen los JSON que genera el pipeline de Python (data/processed/).
// TypeScript estricto las usa para avisar en compilación si accedemos a un campo que
// no existe. Si el analista cambia la forma de un JSON, hay que actualizarlas aquí.
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson';

/** Bloque de trazabilidad común: de dónde salió el dato y cuándo. */
export interface MetadatosBase {
  fuente: string;
  url: string;
  procesado_en: string;
  metodologia?: string;
  unidad?: string;
}

// ─────────────── oni.json ───────────────

export type FaseEnso = 'El Niño' | 'La Niña' | 'Neutral';

export interface PuntoOni {
  trimestre: string; // "ASO"
  anio: number;
  fecha: string; // mes central "2026-09"
  total: number;
  anomalia: number;
  fase: FaseEnso;
}

export interface EventoEnso {
  tipo: 'El Niño' | 'La Niña';
  estado: 'terminado' | 'en curso' | 'en formación';
  inicio: string;
  fin: string;
  duracion_trimestres: number;
  pico: number;
  trimestre_pico: string;
  intensidad: string;
}

export interface ComparacionEventoOni {
  evento: string;
  trimestre_comparado: string;
  anomalia_mismo_trimestre: number | null;
  pico: number | null;
  trimestre_pico: string | null;
  duracion_trimestres: number | null;
}

export interface DatosOni {
  metadatos: MetadatosBase & { descargado_en: string };
  ultimo: {
    trimestre: string;
    fecha: string;
    anomalia: number;
    fase: FaseEnso;
    evento_actual: EventoEnso | null;
  };
  comparacion_eventos: ComparacionEventoOni[];
  eventos: EventoEnso[];
  serie: PuntoOni[];
}

// ─────────────── embalses.json ───────────────

export interface PuntoFecha {
  fecha: string; // "2026-11-03"
  porcentaje: number;
}

export interface Temporada {
  temporada: string; // "2015–16"
  es_actual: boolean;
  serie: (PuntoFecha & { dia: number })[];
  minimo: PuntoFecha | null;
}

export interface DatosEmbalses {
  metadatos: MetadatosBase & { descarga_mas_reciente: string; descarga_mas_antigua: string };
  ultimo: {
    fecha: string;
    porcentaje_sistema: number;
    variacion_7d_pp: number | null;
    variacion_30d_pp: number | null;
  };
  regiones_ultimo: {
    region: string;
    porcentaje: number;
    volumen_util_gwh: number;
    capacidad_util_gwh: number;
    n_embalses: number;
  }[];
  comparacion_temporadas: {
    descripcion: string;
    dia_actual: number;
    misma_altura: { temporada: string; fecha: string | null; porcentaje: number | null }[];
    temporadas: Temporada[];
  };
  serie_sistema: PuntoFecha[];
  serie_regiones: { region: string; serie: PuntoFecha[] }[];
  control_calidad: Record<string, unknown>;
}

// ─────────────── departamentos.geojson ───────────────

export interface PropiedadesDepartamento {
  codigo: string; // código DANE de 2 dígitos
  nombre: string;
}

export type Departamentos = FeatureCollection<Polygon | MultiPolygon, PropiedadesDepartamento> & {
  metadatos: {
    fuentes: { fuente: string; url: string; descargado_en: string }[];
    procesado_en: string;
    notas: string;
  };
};
