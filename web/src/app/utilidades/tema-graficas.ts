// Estilo base de Chart.js compartido por todas las gráficas.
// Gris medio para textos y rejilla: legible en modo claro y oscuro.
import { Chart } from 'chart.js';

Chart.defaults.color = '#868e96';
Chart.defaults.borderColor = 'rgba(134, 142, 150, 0.2)';
Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
Chart.defaults.maintainAspectRatio = false; // el alto lo pone el contenedor CSS
Chart.defaults.animation = false; // series largas: sin animación se siente más rápido

/** Formatea un número con coma decimal (es-CO). */
export const fmt = (n: number, decimales = 1) =>
  n.toLocaleString('es-CO', { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
