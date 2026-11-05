import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  input,
  viewChild,
} from '@angular/core';
import * as L from 'leaflet';

import { Departamentos, PropiedadesDepartamento } from '../../modelos/datos';

// Mapa base de Colombia con límites departamentales (DANE MGN 2025).
// En la fase 3 se le añadirá la capa del índice de riesgo municipal.
@Component({
  selector: 'app-mapa-colombia',
  template: `<div #contenedor class="mapa" role="img" aria-label="Mapa de departamentos de Colombia"></div>`,
  styles: `.mapa { height: 420px; border-radius: 8px; z-index: 0; }`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MapaColombia {
  readonly departamentos = input.required<Departamentos>();

  // viewChild: referencia al <div #contenedor> de la plantilla (signal).
  private readonly contenedor = viewChild.required<ElementRef<HTMLDivElement>>('contenedor');
  private mapa?: L.Map;

  constructor() {
    // afterNextRender: se ejecuta una vez, cuando el HTML ya está en el navegador.
    // Leaflet necesita el <div> real con su tamaño para dibujar.
    afterNextRender(() => this.crearMapa());

    // Al salir de la página, liberar el mapa (eventos, capas, memoria).
    inject(DestroyRef).onDestroy(() => this.mapa?.remove());
  }

  private crearMapa(): void {
    this.mapa = L.map(this.contenedor().nativeElement, { scrollWheelZoom: false });

    // Teselas base de OpenStreetMap: no requieren API key (nunca pondríamos una clave en
    // el frontend: cualquiera la vería). Su política de uso exige la atribución visible.
    // (Se descartó CARTO: ahora exige API key y mostraba "API KEY REQUIRED".)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · Límites: DANE MGN 2025',
      maxZoom: 12,
    }).addTo(this.mapa);

    const capa = L.geoJSON(this.departamentos(), {
      style: { color: '#495057', weight: 1, fillColor: '#74c0fc', fillOpacity: 0.15 },
      onEachFeature: (feature, layer) => {
        const p = feature.properties as PropiedadesDepartamento;
        // Leaflet interpreta un string como HTML; con textContent garantizamos texto plano
        // aunque un dato externo trajera etiquetas (evita inyección de HTML).
        const etiqueta = document.createElement('span');
        etiqueta.textContent = `${p.nombre} (${p.codigo})`;
        layer.bindTooltip(etiqueta, { sticky: true });
        layer.on({
          mouseover: () => (layer as L.Path).setStyle({ fillOpacity: 0.35, weight: 2 }),
          mouseout: () => capa.resetStyle(layer),
        });
      },
    }).addTo(this.mapa);

    // San Andrés queda muy lejos del continente: encuadramos el territorio continental.
    this.mapa.fitBounds([[-4.3, -79.1], [12.6, -66.8]]);
  }
}
