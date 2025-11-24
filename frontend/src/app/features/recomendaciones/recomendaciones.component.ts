import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { RecommendationsService } from '@core/services/recommendations.service';
import { CAMPANAS_DISPONIBLES, CULTIVOS_DISPONIBLES, LOTES_DISPONIBLES } from '@shared/constants/farm.constants';
import {
  BulkSiembraRecommendationRequest,
  BulkSiembraRecommendationResponse,
  BulkSiembraRecommendationItem,
  RecommendationAlternative,
  RecommendationWindow,
  RecommendationPdfRequest,
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
  bulkResult: BulkSiembraRecommendationResponse | null = null;
  error: string | null = null;
  pdfError: string | null = null;
  private readonly downloadingRecommendations = new Set<string>();

  // Debe coincidir con los permitidos por el backend
  readonly cultivos = [...CULTIVOS_DISPONIBLES];
  readonly lotes = LOTES_DISPONIBLES.map((lote) => ({ ...lote }));
  readonly campanas = [...CAMPANAS_DISPONIBLES];

  constructor(
    private readonly fb: FormBuilder,
    private readonly recommendationsService: RecommendationsService
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

    const selectedLotes: string[] = this.recommendationForm.value.loteIds ?? [];
    if (!selectedLotes.length) {
      this.recommendationForm.get('loteIds')?.setErrors({ required: true });
      return;
    }

    const payload = this.buildRequestPayload();
    this.isLoading = true;
    this.error = null;
    this.pdfError = null;
    this.bulkResult = null;

    this.recommendationsService
      .generateSiembraRecommendation(payload)
      .pipe(finalize(() => (this.isLoading = false)))
      .subscribe({
        next: (response) => {
          this.bulkResult = response;
        },
        error: (err) => {
          this.error = err?.message ?? 'No se pudo generar la recomendacion';
        }
      });
  }

  onDownloadResultPdf(response: SiembraRecommendationResponse, loteLabel: string): void {
    const key = this.getRecommendationDownloadKey(response);
    if (this.downloadingRecommendations.has(key)) {
      return;
    }
    this.pdfError = null;
    this.downloadingRecommendations.add(key);

    const payload: RecommendationPdfRequest = {
      recomendacion: response,
      metadata: {
        lote_label: loteLabel
      }
    };

    this.recommendationsService.downloadRecommendationPdf(payload).pipe(
      finalize(() => this.downloadingRecommendations.delete(key))
    ).subscribe({
      next: (blob) => {
        const filename = this.buildResultFilename(response);
        this.triggerFileDownload(blob, filename);
      },
      error: () => {
        this.pdfError = 'No pudimos generar el PDF. Intenta nuevamente.';
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

  formatVentana(ventana?: RecommendationWindow['ventana']): string {
    if (!ventana || ventana.length < 2) {
      return '-';
    }
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
      loteIds: [[this.lotes[0].value], [Validators.required, Validators.minLength(1)]],
      cultivo: [this.cultivos[0], Validators.required],
      campana: [this.defaultCampana, Validators.required]
    });
  }

  private buildRequestPayload(): BulkSiembraRecommendationRequest {
    const { loteIds, cultivo, campana } = this.recommendationForm.value;
    const fecha = new Date();

    return {
      lote_ids: loteIds,
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
    const display = lote ? lote.label : loteId;
    return display ? `Lote ${display}` : 'Lote';
  }

  get successfulResults(): BulkSiembraRecommendationItem[] {
    return this.bulkResult?.resultados.filter((item) => item.success && !!item.response) ?? [];
  }

  get failedResults(): BulkSiembraRecommendationItem[] {
    return this.bulkResult?.resultados.filter((item) => !item.success) ?? [];
  }

  get hasPartialFailures(): boolean {
    return this.failedResults.length > 0;
  }

  getDatosEntradaValue(response: SiembraRecommendationResponse | undefined, key: string): string {
    if (!response?.datos_entrada) {
      return '';
    }
    const value = response.datos_entrada[key];
    if (value === undefined || value === null) {
      return '';
    }
    return String(value);
  }

  isRecommendationDownloading(response: SiembraRecommendationResponse): boolean {
    return this.downloadingRecommendations.has(this.getRecommendationDownloadKey(response));
  }

  private getRecommendationDownloadKey(response: SiembraRecommendationResponse): string {
    return response.prediccion_id ?? `${response.lote_id}-${response.fecha_generacion}`;
  }

  private buildResultFilename(response: SiembraRecommendationResponse): string {
    const lote = this.sanitizeForFile(response.lote_id);
    const campanaValue = response.datos_entrada?.['campana'] as string | undefined;
    const fecha = this.sanitizeForFile(campanaValue ?? response.fecha_generacion);
    return `recomendacion-${lote}-${fecha}.pdf`;
  }

  private triggerFileDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  private sanitizeForFile(value?: string): string {
    if (!value) {
      return 'informe';
    }
    return value.replace(/[^a-z0-9-_]+/gi, '-').toLowerCase();
  }
}
