import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '@core/services/api.service';
import { PredictionResponse, Lote } from '@shared/models/predictions.model';

@Component({
  selector: 'app-recomendaciones',
  templateUrl: './recomendaciones.component.html',
  styleUrls: ['./recomendaciones.component.scss']
})
export class RecomendacionesComponent implements OnInit {
  predictionForm: FormGroup;
  selectedPredictionType: string = 'siembra';
  isLoading = false;
  result: PredictionResponse | null = null;
  error: string | null = null;
  lotes: Lote[] = [];

  predictionTypes = [
    { value: 'siembra', label: 'Fechas de Siembra' },
    { value: 'variedades', label: 'Selección de Variedades' },
    { value: 'rendimiento', label: 'Predicción de Rendimiento' },
    { value: 'fertilizacion', label: 'Plan de Fertilización' },
    { value: 'clima', label: 'Predicción Climática' },
    { value: 'cosecha', label: 'Momento de Cosecha' }
  ];

  cultivos = ['trigo', 'soja', 'maiz', 'cebada', 'girasol'];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService
  ) {
    this.predictionForm = this.createForm();
  }

  ngOnInit(): void {
    this.loadLotes();
  }

  createForm(): FormGroup {
    return this.fb.group({
      predictionType: ['siembra', Validators.required],
      loteId: ['lote-001', Validators.required],
      clienteId: ['cliente-001', Validators.required],
      cultivo: ['trigo', Validators.required],
      campana: ['2024/2025'],
      fechaSiembra: [''],
      variedad: [''],
      objetivoRendimiento: [''],
      latitud: [-34.5],
      longitud: [-58.5],
      fechaDesde: [''],
      fechaHasta: ['']
    });
  }

  loadLotes(): void {
    this.apiService.getLotes().subscribe({
      next: (data) => {
        this.lotes = data;
      },
      error: (err) => {
        console.error('Error loading lotes:', err);
      }
    });
  }

  onPredictionTypeChange(): void {
    this.selectedPredictionType = this.predictionForm.get('predictionType')?.value;
    this.result = null;
    this.error = null;
  }

  onSubmit(): void {
    if (this.predictionForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.error = null;
    this.result = null;

    const formValue = this.predictionForm.value;
    const predictionData = this.preparePredictionData(formValue);

    let prediction$;

    switch (this.selectedPredictionType) {
      case 'siembra':
        prediction$ = this.apiService.predictSiembra(predictionData);
        break;
      case 'variedades':
        prediction$ = this.apiService.predictVariedades(predictionData);
        break;
      case 'rendimiento':
        prediction$ = this.apiService.predictRendimiento(predictionData);
        break;
      case 'fertilizacion':
        prediction$ = this.apiService.predictFertilizacion(predictionData);
        break;
      case 'clima':
        prediction$ = this.apiService.predictClima(predictionData);
        break;
      case 'cosecha':
        prediction$ = this.apiService.predictCosecha(predictionData);
        break;
      default:
        this.error = 'Tipo de predicción no válido';
        this.isLoading = false;
        return;
    }

    prediction$.subscribe({
      next: (response) => {
        this.result = response;
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.message || 'Error al generar la predicción';
        this.isLoading = false;
      }
    });
  }

  preparePredictionData(formValue: any): any {
    const baseData = {
      lote_id: formValue.loteId,
      cliente_id: formValue.clienteId,
      cultivo: formValue.cultivo
    };

    switch (this.selectedPredictionType) {
      case 'siembra':
        return { ...baseData, campana: formValue.campana };
      case 'variedades':
        return { ...baseData };
      case 'rendimiento':
        return { ...baseData, fecha_siembra: formValue.fechaSiembra, variedad: formValue.variedad };
      case 'fertilizacion':
        return { ...baseData, objetivo_rendimiento: formValue.objetivoRendimiento };
      case 'clima':
        return {
          latitud: formValue.latitud,
          longitud: formValue.longitud,
          fecha_desde: formValue.fechaDesde,
          fecha_hasta: formValue.fechaHasta
        };
      case 'cosecha':
        return { ...baseData, fecha_siembra: formValue.fechaSiembra, variedad: formValue.variedad };
      default:
        return baseData;
    }
  }

  getConfidenceClass(confidence: number): string {
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.6) return 'confidence-medium';
    return 'confidence-low';
  }

  getConfidenceLabel(confidence: number): string {
    if (confidence >= 0.8) return 'Alta';
    if (confidence >= 0.6) return 'Media';
    return 'Baja';
  }
}