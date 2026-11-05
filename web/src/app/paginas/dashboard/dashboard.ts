import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';

import { FuenteDato } from '../../componentes/fuente-dato/fuente-dato';
import { GraficaEmbalses } from '../../componentes/grafica-embalses/grafica-embalses';
import { GraficaOni } from '../../componentes/grafica-oni/grafica-oni';
import { GraficaRegiones } from '../../componentes/grafica-regiones/grafica-regiones';
import { MapaColombia } from '../../componentes/mapa-colombia/mapa-colombia';
import { TarjetaIndicador } from '../../componentes/tarjeta-indicador/tarjeta-indicador';
import { DatosService } from '../../servicios/datos.service';
import { colorFase, COLORES } from '../../utilidades/temporada';
import { fmt } from '../../utilidades/tema-graficas';

// Página principal. Es un componente "contenedor": obtiene los datos del servicio y los
// reparte a componentes presentacionales (tarjetas, gráficas, mapa) mediante inputs.
@Component({
  selector: 'app-dashboard',
  imports: [
    DecimalPipe,
    FuenteDato,
    GraficaEmbalses,
    GraficaOni,
    GraficaRegiones,
    MapaColombia,
    TarjetaIndicador,
  ],
  // Providers a nivel de componente: Chart.js se registra aquí (y lo heredan las
  // gráficas hijas) para que viaje en el paquete lazy del dashboard, no en el inicial.
  providers: [provideCharts(withDefaultRegisterables())],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Dashboard {
  // inject(): forma moderna de pedir un servicio (en vez de ponerlo en el constructor).
  protected readonly datos = inject(DatosService);
  protected readonly fmt = fmt;

  // Valores derivados para las tarjetas. computed() evita recalcular en cada repintado.
  protected readonly tarjetaOni = computed(() => {
    const oni = this.datos.oni.value();
    if (!oni) return null;
    const u = oni.ultimo;
    const evento = u.evento_actual;
    return {
      valor: `${u.anomalia > 0 ? '+' : ''}${fmt(u.anomalia, 2)} °C`,
      detalle: evento
        ? `${evento.tipo} ${evento.intensidad} (${evento.estado}) · ${u.trimestre}`
        : `${u.fase} · ${u.trimestre}`,
      acento: colorFase(u.fase),
    };
  });

  protected readonly tarjetaEmbalses = computed(() => {
    const e = this.datos.embalses.value();
    if (!e) return null;
    const v7 = e.ultimo.variacion_7d_pp;
    return {
      valor: `${fmt(e.ultimo.porcentaje_sistema)} %`,
      detalle:
        v7 === null
          ? `Sistema al ${e.ultimo.fecha}`
          : `${v7 >= 0 ? '+' : ''}${fmt(v7, 2)} pp en 7 días · ${e.ultimo.fecha}`,
    };
  });

  protected readonly mismaAltura = computed(
    () => this.datos.embalses.value()?.comparacion_temporadas.misma_altura ?? [],
  );

  protected readonly fuenteOni = computed(() => {
    const m = this.datos.oni.value()?.metadatos;
    return m ? [{ fuente: m.fuente, url: m.url, descargado_en: m.descargado_en }] : [];
  });

  protected readonly fuenteEmbalses = computed(() => {
    const m = this.datos.embalses.value()?.metadatos;
    return m ? [{ fuente: m.fuente, url: m.url, descargado_en: m.descarga_mas_reciente }] : [];
  });

  protected readonly COLORES = COLORES;
}
