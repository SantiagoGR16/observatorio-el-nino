import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { DatosEmbalses } from '../../modelos/datos';
import { fmt } from '../../utilidades/tema-graficas';

type Region = DatosEmbalses['regiones_ultimo'][number];

// Barras horizontales: % de volumen útil por región hidrológica (ponderado por capacidad).
@Component({
  selector: 'app-grafica-regiones',
  imports: [BaseChartDirective],
  template: `
    <div class="lienzo">
      <canvas baseChart type="bar" [data]="datos()" [options]="opciones"></canvas>
    </div>
  `,
  styles: `.lienzo { position: relative; height: 280px; }`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GraficaRegiones {
  readonly regiones = input.required<Region[]>();

  protected readonly datos = computed<ChartConfiguration<'bar'>['data']>(() => ({
    labels: this.regiones().map((r) => this.titulo(r.region)),
    datasets: [
      {
        label: '% volumen útil',
        data: this.regiones().map((r) => r.porcentaje),
        // Más bajo = más preocupante: rojo < 40 %, ámbar < 60 %, azul en otro caso.
        backgroundColor: this.regiones().map((r) =>
          r.porcentaje < 40 ? '#e03131' : r.porcentaje < 60 ? '#f59f00' : '#1c7ed6',
        ),
        borderRadius: 4,
      },
    ],
  }));

  protected readonly opciones: ChartConfiguration<'bar'>['options'] = {
    indexAxis: 'y', // barras horizontales
    scales: { x: { min: 0, max: 100, title: { display: true, text: '%' } } },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (item) => {
            const r = this.regiones()[item.dataIndex];
            return [
              `${fmt(r.porcentaje)} % · ${r.n_embalses} embalses`,
              `${fmt(r.volumen_util_gwh, 0)} de ${fmt(r.capacidad_util_gwh, 0)} GWh`,
            ];
          },
        },
      },
    },
  };

  private titulo(texto: string): string {
    return texto.charAt(0) + texto.slice(1).toLowerCase();
  }
}
