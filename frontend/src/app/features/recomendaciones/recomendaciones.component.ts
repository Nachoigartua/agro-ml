import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { RecommendationsService } from '@core/services/recommendations.service';
import { CAMPANAS_DISPONIBLES, CULTIVOS_DISPONIBLES, LOTES_DISPONIBLES } from '@shared/constants/farm.constants';
import {
  BulkSiembraRecommendationRequest,
  BulkSiembraRecommendationResponse,
  BulkSiembraRecommendationItem,
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

}
