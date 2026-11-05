// Configuración global de la aplicación.
// En Angular "standalone" no hay AppModule: los servicios globales (providers) se
// registran aquí y main.ts los pasa a bootstrapApplication().
import { registerLocaleData } from '@angular/common';
import { provideHttpClient, withFetch } from '@angular/common/http';
import localeEsCo from '@angular/common/locales/es-CO';
import {
  ApplicationConfig,
  LOCALE_ID,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { routes } from './app.routes';

// Datos de idioma para que los pipes (number, date) formateen a la colombiana:
// 77.84 -> "77,84" y fechas como "3 nov 2026".
registerLocaleData(localeEsCo);

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    // HttpClient para leer los JSON de /data. withFetch() usa la API fetch del navegador.
    provideHttpClient(withFetch()),
    // Nota: Chart.js NO se registra aquí sino en el componente Dashboard, para que
    // quede en el paquete diferido (lazy) y no en la carga inicial.
    { provide: LOCALE_ID, useValue: 'es-CO' },
  ],
};
