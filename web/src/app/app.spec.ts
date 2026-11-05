// Prueba del componente raíz con TestBed (el "banco de pruebas" de Angular) y Vitest.
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      // Router vacío: aquí solo probamos el marco, no las páginas.
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('muestra el título del observatorio', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const html = fixture.nativeElement as HTMLElement;
    expect(html.querySelector('h1')?.textContent).toContain('Observatorio de El Niño');
  });

  it('enlaza al repositorio en el pie', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const enlace = (fixture.nativeElement as HTMLElement).querySelector('footer a');
    expect(enlace?.getAttribute('href')).toContain('github.com/SantiagoGR16/observatorio-el-nino');
  });
});
