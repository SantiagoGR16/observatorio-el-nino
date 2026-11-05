import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { PuntoOni } from '../../modelos/datos';
import { colorAnomalia, COLORES } from '../../utilidades/temporada';
import { fmt } from '../../utilidades/tema-graficas';

type Rango = 1950 | 1997;

// Línea del ONI con umbrales ±0.5 °C. Cada tramo se colorea según la fase:
// naranja = El Niño, azul = La Niña, gris = neutral.
@Component({
  selector: 'app-grafica-oni',
  imports: [BaseChartDirective],
  template: `
    <div class="controles" role="group" aria-label="Rango de años">
      @for (r of rangos; track r) {
        <button type="button" [class.activo]="desde() === r" (click)="desde.set(r)">
          Desde {{ r }}
        </button>
      }
    </div>
    <div class="lienzo">
      <canvas baseChart type="line" [data]="datos()" [options]="opciones"></canvas>
    </div>
  `,
  styles: `
    .lienzo { position: relative; height: 320px; }
    .controles { display: flex; gap: .5rem; margin-bottom: .75rem; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GraficaOni {
  readonly serie = input.required<PuntoOni[]>();

  protected readonly rangos: Rango[] = [1997, 1950];
  // signal() = estado local que se puede cambiar con .set(); la plantilla reacciona sola.
  protected readonly desde = signal<Rango>(1997);

  // computed(): se recalcula solo cuando cambian serie() o desde().
  protected readonly datos = computed<ChartConfiguration<'line'>['data']>(() => {
    const puntos = this.serie().filter((p) => p.anio >= this.desde());
    const umbral = (v: number) => puntos.map(() => v);
    return {
      labels: puntos.map((p) => `${p.trimestre} ${p.anio}`),
      datasets: [
        {
          label: 'Anomalía ONI (°C)',
          data: puntos.map((p) => p.anomalia),
          borderWidth: 2,
          pointRadius: 0,
          // segment: color de cada tramo según el valor al que llega.
          segment: { borderColor: (ctx) => colorAnomalia(ctx.p1.parsed.y ?? 0) },
          borderColor: COLORES.neutral,
        },
        { label: 'Umbral El Niño (+0,5)', data: umbral(0.5), borderColor: COLORES.nino,
          borderDash: [4, 4], borderWidth: 1, pointRadius: 0 },
        { label: 'Umbral La Niña (−0,5)', data: umbral(-0.5), borderColor: COLORES.nina,
          borderDash: [4, 4], borderWidth: 1, pointRadius: 0 },
      ],
    };
  });

  protected readonly opciones: ChartConfiguration<'line'>['options'] = {
    interaction: { mode: 'index', intersect: false },
    scales: {
      x: { ticks: { maxTicksLimit: 12, maxRotation: 0 } },
      y: { title: { display: true, text: '°C' } },
    },
    plugins: {
      legend: { position: 'bottom', labels: { boxHeight: 2 } },
      tooltip: {
        filter: (item) => item.datasetIndex === 0,
        callbacks: { label: (item) => `Anomalía: ${fmt(item.parsed.y ?? 0, 2)} °C` },
      },
    },
  };
}
