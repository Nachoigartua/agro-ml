import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { RecommendationsService } from '@core/services/recommendations.service';
import { PdfDownloadService } from '@core/services/pdf-download.service';
import { CAMPANAS_DISPONIBLES, CULTIVOS_DISPONIBLES, LOTES_DISPONIBLES } from '@shared/constants/farm.constants';
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
  isDownloadingPdf = false;

  // Debe coincidir con los permitidos por el backend
  readonly cultivos = [...CULTIVOS_DISPONIBLES];
  readonly lotes = LOTES_DISPONIBLES.map((lote) => ({ ...lote }));
  readonly campanas = [...CAMPANAS_DISPONIBLES];

  constructor(
    private readonly fb: FormBuilder,
    private readonly recommendationsService: RecommendationsService,
    private readonly pdfDownloadService: PdfDownloadService
  ) {
    this.recommendationForm = this.createForm();
  }

  ngOnInit(): void {}

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

  /**
   * Descarga el PDF de la recomendación actual
   */
  downloadPdf(): void {
    if (!this.result) {
      console.warn('No hay recomendación para descargar');
      return;
    }

    // Obtener el ID de la predicción desde la respuesta del servidor
    const prediccionId = this.result.prediccion_id;
    if (!prediccionId) {
      console.error('No se encontró el ID de predicción en la respuesta');
      alert('No se pudo obtener el ID de la predicción. Por favor, intenta nuevamente.');
      return;
    }
    
    this.isDownloadingPdf = true;
    
    this.pdfDownloadService
      .downloadRecommendationPdf(prediccionId, this.result.cultivo)
      .pipe(finalize(() => (this.isDownloadingPdf = false)))
      .subscribe({
        next: (blob: Blob) => {
          const filename = `recomendacion_${this.result!.cultivo}_${new Date().getTime()}.pdf`;
          this.pdfDownloadService.triggerDownload(blob, filename);
        },
        error: (err: any) => {
          console.error('Error al descargar PDF:', err);
          alert('No se pudo descargar el PDF. Por favor, intenta nuevamente.');
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
      cliente_id: '123e4567-e89b-12d3-a456-426614174001'
    };
  }

  formatDate(value: string): string {
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

  getLoteLabel(loteId: string): string {
    const lote = this.lotes.find(l => l.value === loteId);
    return lote ? lote.label : loteId;
  }

  getDatosEntradaLoteId(): string {
    return this.result?.datos_entrada?.['lote_id'] as string || '';
  }

  getDatosEntradaCampana(): string {
    return this.result?.datos_entrada?.['campana'] as string || '';
  }

  getDatosEntradaFechaConsulta(): string {
    return this.result?.datos_entrada?.['fecha_consulta'] as string || '';
  }
}