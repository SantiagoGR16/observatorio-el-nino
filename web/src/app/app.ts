import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

// Componente raíz: el "marco" de la app (encabezado + contenido + pie).
// <router-outlet> es donde el router pinta la página de la ruta activa.
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  protected readonly repositorio = 'https://github.com/SantiagoGR16/observatorio-el-nino';
}
