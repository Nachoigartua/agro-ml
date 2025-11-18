import { Component, Input } from '@angular/core';
import { RecommendationAlternative, RecommendationWindow, SiembraRecommendationResponse } from '@shared/models/recommendations.model';

@Component({
  selector: 'app-siembra-recommendation-detail',
  templateUrl: './siembra-recommendation-detail.component.html',
  styleUrls: ['./siembra-recommendation-detail.component.scss']
})
export class SiembraRecommendationDetailComponent {
  @Input({ required: true }) recommendation!: SiembraRecommendationResponse;
  @Input() loteLabel?: string;

  trackByAlternative(_: number, item: RecommendationAlternative): string {
    return `${item.fecha}-${item.confianza}`;
  }

  formatVentana(ventana?: RecommendationWindow['ventana']): string {
    if (!ventana || ventana.length < 2) {
      return '—';
    }
    const [inicio, fin] = ventana;
    return `${this.formatDate(inicio)} - ${this.formatDate(fin)}`;
  }

  formatDate(value?: string): string {
    if (!value) {
      return '—';
    }
    const ddmmyyyy = /^\d{2}-\d{2}-\d{4}$/;
    if (ddmmyyyy.test(value)) {
      const [dd, mm, yyyy] = value.split('-');
      return `${dd}/${mm}/${yyyy}`;
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    try {
      return new Intl.DateTimeFormat('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        timeZone: 'America/Argentina/Buenos_Aires'
      }).format(date);
    } catch {
      return date.toLocaleDateString('es-AR');
    }
  }

  formatDateTime(value?: string): string {
    if (!value) {
      return '';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    try {
      return new Intl.DateTimeFormat('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZone: 'America/Argentina/Buenos_Aires'
      }).format(date);
    } catch {
      return date.toLocaleString('es-AR');
    }
  }

  getDatosEntradaValue(key: string): string {
    const value = this.recommendation?.datos_entrada?.[key];
    if (value === null || value === undefined) {
      return '';
    }
    return String(value);
  }

  get computedLoteLabel(): string {
    if (this.loteLabel) {
      return this.loteLabel;
    }
    return this.recommendation?.lote_id ? `Lote ${this.recommendation.lote_id}` : 'Lote';
  }

  get hasAlternatives(): boolean {
    return Array.isArray(this.recommendation?.alternativas) && this.recommendation.alternativas.length > 0;
  }

  get hasCosts(): boolean {
    return !!this.recommendation?.costos_estimados && Object.keys(this.recommendation.costos_estimados).length > 0;
  }

}
