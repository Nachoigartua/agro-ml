import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { ApiService } from '@core/services/api.service';
import { RecommendationsService } from '@core/services/recommendations.service';
import {
  Lote,
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
  private readonly defaultCampana = '2024/2025';

  recommendationForm: FormGroup;
  isLoading = false;
  result: SiembraRecommendationResponse | null = null;
  error: string | null = null;
  lotes: Lote[] = [];

  // Debe coincidir con los permitidos por el backend
  readonly cultivos = ['trigo', 'soja', 'maiz', 'cebada'];

  constructor(
    private readonly fb: FormBuilder,
    private readonly apiService: ApiService,
    private readonly recommendationsService: RecommendationsService
  ) {
    this.recommendationForm = this.createForm();
  }

  ngOnInit(): void {
    this.loadLotes();
  }

  resetForm(): void {
    const current = this.recommendationForm.value;
    this.recommendationForm.reset({
      loteId: current.loteId ?? 'lote-001',
      clienteId: current.clienteId ?? 'cliente-001',
      cultivo: this.cultivos[0],
      campana: this.defaultCampana,
      fechaConsulta: this.getTodayIso()
    });
    this.recommendationForm.markAsPristine();
    this.recommendationForm.markAsUntouched();
  }

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
    return `${item.fecha_optima}-${item.justificacion ?? 'alt'}`;
  }

  formatDateTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
  }

  private createForm(): FormGroup {
    return this.fb.group({
      // Usar UUIDs válidos por defecto para evitar 422
      loteId: ['123e4567-e89b-12d3-a456-426614174000', Validators.required],
      clienteId: ['123e4567-e89b-12d3-a456-426614174001', Validators.required],
      cultivo: [this.cultivos[0], Validators.required],
      campana: [this.defaultCampana, Validators.required],
      fechaConsulta: [this.getTodayIso(), Validators.required]
    });
  }

  private loadLotes(): void {
    this.apiService.getLotes().subscribe({
      next: (data) => {
        this.lotes = data ?? [];
        if (this.lotes.length > 0) {
          const firstLote = this.lotes[0];
          this.recommendationForm.patchValue({
            loteId: firstLote.id,
            clienteId: firstLote.cliente_id
          });
        } else {
          // Si no hay lotes (no hay endpoint mock), mantener UUIDs válidos
        }
      },
      error: (err) => {
        console.error('Error loading lotes:', err);
        // Mantener los UUIDs por defecto
      }
    });
  }

  private buildRequestPayload(): SiembraRecommendationRequest {
    const { loteId, clienteId, cultivo, campana, fechaConsulta } = this.recommendationForm.value;
    const fecha = fechaConsulta ? new Date(fechaConsulta) : new Date();

    return {
      lote_id: loteId,
      cliente_id: clienteId,
      cultivo,
      campana,
      fecha_consulta: fecha.toISOString()
    };
  }

  formatDate(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleDateString();
  }

  private getTodayIso(): string {
    return new Date().toISOString().substring(0, 10);
  }
}
