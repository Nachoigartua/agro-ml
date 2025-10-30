import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { RecommendationsService } from '@core/services/recommendations.service';
import {
  RecommendationAlternative,
  RecommendationWindow,
  SiembraRecommendationRequest,
  SiembraRecommendationResponse
} from '@shared/models/recommendations.model';

@Component({
  selector: 'app-recomendaciones',
  templateUrl: './recomendaciones.component.html',
  styleUrls: ['./recomendaciones.component.scss']
})
export class RecomendacionesComponent implements OnInit {
  private readonly defaultCampana = '2025/2026';

  recommendationForm: FormGroup;
  isLoading = false;
  result: SiembraRecommendationResponse | null = null;
  error: string | null = null;

  // Debe coincidir con los permitidos por el backend
  readonly cultivos = ['trigo', 'soja', 'maiz', 'cebada'];
  readonly lotes = [
    { label: 'lote-001', value: 'c3f2f1ab-ca2e-4f8b-9819-377102c4d889' },
    { label: 'lote-002', value: 'f6c1d3e9-4aa7-4b24-8b1c-65f06e3f4d30' }
  ];

  constructor(
    private readonly fb: FormBuilder,
    private readonly recommendationsService: RecommendationsService
  ) {
    this.recommendationForm = this.createForm();
  }

  ngOnInit(): void {}

  // resetForm button removed; keeping minimal form inputs

  onCultivoSelect(cultivo: string): void {
    this.recommendationForm.patchValue({ cultivo });
  }

  onSubmit(): void {
    if (this.recommendationForm.invalid) {
      this.recommendationForm.markAllAsTouched();
      return;
    }

    const payload = this.buildRequestPayload();
    this.isLoading = true;
    this.error = null;
    this.result = null;

    this.recommendationsService
      .generateSiembraRecommendation(payload)
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (response) => {
          this.result = response;
        },
        error: (err) => {
          this.error = err?.message ?? 'No se pudo generar la recomendacion';
        }
      });
  }

  getConfidenceClass(confidence: number): string {
    if (confidence >= 0.8) {
      return 'confidence-high';
    }

    if (confidence >= 0.6) {
      return 'confidence-medium';
    }

    return 'confidence-low';
  }

  getConfidenceLabel(confidence: number): string {
    if (confidence >= 0.8) {
      return 'Alta';
    }

    if (confidence >= 0.6) {
      return 'Media';
    }

    return 'Baja';
  }

  formatVentana(ventana: RecommendationWindow['ventana']): string {
    const [inicio, fin] = ventana;
    return `${this.formatDate(inicio)} - ${this.formatDate(fin)}`;
  }

  trackByAlternative(_: number, item: RecommendationAlternative): string {
    return `${item.fecha}-${item.confianza}`;
  }

  formatDateTime(value: string): string {
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

  private createForm(): FormGroup {
    return this.fb.group({
      // Usar UUIDs válidos por defecto para evitar 422
      loteId: [this.lotes[0].value, Validators.required],
      cultivo: [this.cultivos[0], Validators.required],
      campana: [this.defaultCampana, Validators.required]
    });
  }

  private buildRequestPayload(): SiembraRecommendationRequest {
    const { loteId, cultivo, campana } = this.recommendationForm.value;
    const fecha = new Date();

    return {
      lote_id: loteId,
      cultivo,
      campana,
      fecha_consulta: fecha.toISOString(),
      // por ahora se envía un cliente fijo; luego vendrá de la sesión
      cliente_id: '123e4567-e89b-12d3-a456-426614174001'
    };
  }

  formatDate(value: string): string {
    // El backend envía fechas de ventana y óptima como dd-mm-yyyy.
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
}
