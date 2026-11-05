import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { Temporada } from '../../modelos/datos';
import { COLORES, etiquetaMesTemporada, INICIO_MES_TEMPORADA } from '../../utilidades/temporada';
import { fmt } from '../../utilidades/tema-graficas';

const PALETA_PREVIAS = [COLORES.previa1, COLORES.previa2];

// Nivel del sistema en temporadas El Niño superpuestas, alineadas desde el 1 de julio.
// Eje X numérico (días desde el 1 de julio) para que el día 125 de 2015 caiga sobre
// el día 125 de 2026, sin importar el año.
@Component({
  selector: 'app-grafica-embalses',
  imports: [BaseChartDirective],
  template: `
    <div class="lienzo">
      <canvas baseChart type="line" [data]="datos()" [options]="opciones"></canvas>
    </div>
  `,
  styles: `.lienzo { position: relative; height: 340px; }`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GraficaEmbalses {
  readonly temporadas = input.required<Temporada[]>();

  protected readonly datos = computed<ChartConfiguration<'line'>['data']>(() => {
    let i = 0;
    return {
      datasets: this.temporadas().map((t) => {
        const color = t.es_actual ? COLORES.actual : PALETA_PREVIAS[i++ % PALETA_PREVIAS.length];
        return {
          label: `El Niño ${t.temporada}${t.es_actual ? ' (actual)' : ''}`,
          // Formato {x, y}: Chart.js ubica cada punto por su valor en el eje X.
          data: t.serie.map((p) => ({ x: p.dia, y: p.porcentaje })),
          borderColor: color,
          backgroundColor: color,
          borderWidth: t.es_actual ? 3 : 1.75,
          pointRadius: 0,
        };
      }),
    };
  });

  protected readonly opciones: ChartConfiguration<'line'>['options'] = {
    interaction: { mode: 'nearest', axis: 'x', intersect: false },
    scales: {
      x: {
        type: 'linear',
        min: 0,
        max: 365,
        // Una marca al inicio de cada mes (jul, ago, ... jun).
        afterBuildTicks: (eje) => {
          eje.ticks = INICIO_MES_TEMPORADA.map((value) => ({ value }));
        },
        ticks: { callback: (valor) => etiquetaMesTemporada(Number(valor)) },
      },
      y: { min: 0, max: 100, title: { display: true, text: '% volumen útil' } },
    },
    plugins: {
      legend: { position: 'bottom' },
      tooltip: {
        callbacks: {
          title: () => '',
          label: (item) => {
            const t = this.temporadas()[item.datasetIndex];
            const p = t.serie[item.dataIndex];
            return `${t.temporada} · ${p.fecha}: ${fmt(p.porcentaje)} %`;
          },
        },
      },
    },
  };
}
