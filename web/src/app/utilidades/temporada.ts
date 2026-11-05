// Funciones puras (sin Angular) para ejes y colores: fáciles de probar con Vitest.
import { FaseEnso } from '../modelos/datos';

/** Días desde el 1 de julio en que empieza cada mes (año no bisiesto). */
export const INICIO_MES_TEMPORADA = [0, 31, 62, 92, 123, 153, 184, 215, 243, 274, 304, 335];
const MESES_TEMPORADA = ['jul', 'ago', 'sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar', 'abr', 'may', 'jun'];

/** Etiqueta del eje X para un "día de temporada" (0 = 1 de julio). */
export function etiquetaMesTemporada(dia: number): string {
  const i = INICIO_MES_TEMPORADA.indexOf(dia);
  return i >= 0 ? MESES_TEMPORADA[i] : '';
}

/** Color de una anomalía ONI según el umbral de ±0.5 °C. */
export function colorAnomalia(anomalia: number): string {
  if (anomalia >= 0.5) return COLORES.nino;
  if (anomalia <= -0.5) return COLORES.nina;
  return COLORES.neutral;
}

export function colorFase(fase: FaseEnso): string {
  return fase === 'El Niño' ? COLORES.nino : fase === 'La Niña' ? COLORES.nina : COLORES.neutral;
}

// Colores de tono medio: se leen bien sobre fondo claro y oscuro.
export const COLORES = {
  nino: '#d9480f', // naranja-rojo: calor
  nina: '#1c7ed6', // azul: frío
  neutral: '#868e96',
  actual: '#d9480f',
  previa1: '#5c7cfa',
  previa2: '#20c997',
};
