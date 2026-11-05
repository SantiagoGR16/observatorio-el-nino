import { ChangeDetectionStrategy, Component, input } from '@angular/core';

// Tarjeta con una cifra destacada. Es "presentacional": no pide datos, solo muestra
// lo que el padre le pasa por inputs. Eso la hace reutilizable y fácil de probar.
@Component({
  selector: 'app-tarjeta-indicador',
  template: `
    <article class="tarjeta" [style.--acento]="acento()">
      <h3>{{ titulo() }}</h3>
      @if (valor()) { <p class="valor">{{ valor() }}</p> }
      @if (detalle()) { <p class="detalle">{{ detalle() }}</p> }
      <!-- ng-content: aquí se inserta lo que el padre ponga entre las etiquetas -->
      <ng-content />
    </article>
  `,
  styles: `
    .tarjeta {
      background: var(--superficie);
      border: 1px solid var(--borde);
      border-top: 4px solid var(--acento, var(--texto-suave));
      border-radius: 10px;
      padding: 1rem 1.25rem;
      height: 100%;
    }
    h3 { margin: 0; font-size: 0.85rem; font-weight: 600; color: var(--texto-suave); text-transform: uppercase; letter-spacing: .04em; }
    .valor { margin: .35rem 0 .15rem; font-size: 2.1rem; font-weight: 700; font-variant-numeric: tabular-nums; }
    .detalle { margin: 0; color: var(--texto-suave); }
  `,
  // OnPush: Angular solo vuelve a pintar el componente cuando cambian sus inputs/signals.
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TarjetaIndicador {
  readonly titulo = input.required<string>();
  readonly valor = input<string>('');
  readonly detalle = input<string>('');
  readonly acento = input<string>('');
}
