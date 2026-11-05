// Pruebas de funciones puras: no necesitan TestBed, son TypeScript normal.
import { colorAnomalia, COLORES, etiquetaMesTemporada, INICIO_MES_TEMPORADA } from './temporada';

describe('etiquetaMesTemporada', () => {
  it('el día 0 es julio y el 184 es enero', () => {
    expect(etiquetaMesTemporada(0)).toBe('jul');
    expect(etiquetaMesTemporada(123)).toBe('nov');
    expect(etiquetaMesTemporada(184)).toBe('ene');
  });

  it('días que no son inicio de mes no llevan etiqueta', () => {
    expect(etiquetaMesTemporada(125)).toBe('');
  });

  it('los inicios de mes coinciden con el calendario real (1 jul 2026 + días)', () => {
    const meses = INICIO_MES_TEMPORADA.map((d) => {
      const f = new Date(Date.UTC(2026, 6, 1 + d));
      return `${f.getUTCMonth() + 1}-${f.getUTCDate()}`;
    });
    expect(meses).toEqual(['7-1', '8-1', '9-1', '10-1', '11-1', '12-1', '1-1', '2-1', '3-1', '4-1', '5-1', '6-1']);
  });
});

describe('colorAnomalia', () => {
  it('usa el umbral de ±0,5 °C', () => {
    expect(colorAnomalia(0.5)).toBe(COLORES.nino);
    expect(colorAnomalia(0.49)).toBe(COLORES.neutral);
    expect(colorAnomalia(-0.5)).toBe(COLORES.nina);
  });
});
