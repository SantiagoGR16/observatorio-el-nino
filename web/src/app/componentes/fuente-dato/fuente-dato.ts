import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export interface Fuente {
  fuente: string;
  url: string;
  descargado_en: string; // ISO 8601 UTC
}

// Pie de trazabilidad: regla del proyecto "toda cifra debe poder rastrearse a su fuente".
// Se pone debajo de cada gráfica con los metadatos del JSON correspondiente.
@Component({
  selector: 'app-fuente-dato',
  imports: [DatePipe],
  template: `
    <p class="fuente">
      @for (f of fuentes(); track f.url; let ultimo = $last) {
        Fuente: <a [href]="f.url" target="_blank" rel="noopener">{{ f.fuente }}</a>
        · descargado el {{ f.descargado_en | date: 'd MMM y, HH:mm' : 'America/Bogota' }}
        @if (!ultimo) { <br /> }
      }
      @if (nota()) { <br /><span class="nota">{{ nota() }}</span> }
    </p>
  `,
  styles: `
    .fuente { margin: .75rem 0 0; font-size: .78rem; color: var(--texto-suave); line-height: 1.5; }
    a { color: inherit; }
    .nota { font-style: italic; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FuenteDato {
  readonly fuentes = input.required<Fuente[]>();
  readonly nota = input<string>('');
}
