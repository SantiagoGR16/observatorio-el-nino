import { Routes } from '@angular/router';

// Rutas de la app. `loadComponent` hace "lazy loading": el código del dashboard
// (con Chart.js y Leaflet, que pesan) se descarga en un archivo aparte solo cuando
// se visita la ruta. Así la carga inicial es más liviana.
// En la fase 3 se agregará la ruta 'boletin'.
export const routes: Routes = [
  {
    path: '',
    title: 'Observatorio El Niño 2026–2027',
    loadComponent: () => import('./paginas/dashboard/dashboard').then((m) => m.Dashboard),
  },
  { path: '**', redirectTo: '' },
];
