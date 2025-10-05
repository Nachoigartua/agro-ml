import { Component, OnInit } from '@angular/core';
import { ApiService } from '@core/services/api.service';
import { HealthStatusResponse, ModelStatus, ModelsDashboardState } from '@shared/models/recommendations.model';

type ModelsMap = Record<string, ModelStatus>;

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  modelsStatus: ModelsDashboardState | null = null;
  isLoading = true;
  error: string | null = null;
  healthStatus: HealthStatusResponse | null = null;

  constructor(private readonly apiService: ApiService) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.isLoading = true;
    this.error = null;

    this.apiService.healthCheck().subscribe({
      next: (data) => {
        this.healthStatus = data;
      },
      error: (err) => {
        console.error('Error loading health status:', err);
        this.healthStatus = null;
      }
    });

    this.apiService.getModelsStatus().subscribe({
      next: (data) => {
        this.modelsStatus = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.error = 'Error al cargar el estado de los modelos';
        this.isLoading = false;
        console.error('Error loading models status:', err);
      }
    });
  }

  triggerTraining(modelName: string): void {
    if (!confirm(`Desea entrenar el modelo ${modelName}? Este proceso puede demorar unos minutos.`)) {
      return;
    }

    this.isLoading = true;

    this.apiService.triggerModelTraining(modelName, { force_retrain: true }).subscribe({
      next: () => {
        alert(`Modelo ${modelName} entrenado exitosamente`);
        this.loadDashboardData();
      },
      error: (err) => {
        alert(`Error al entrenar el modelo: ${err.message}`);
        this.isLoading = false;
      }
    });
  }

  getModelsList(): string[] {
    const models = this.modelsStatus?.models as ModelsMap | undefined;
    return models ? Object.keys(models) : [];
  }

  getModelInfo(modelName: string): ModelStatus {
    const models = this.modelsStatus?.models as ModelsMap | undefined;
    return models?.[modelName] ?? ({} as ModelStatus);
  }

  getModelStatusText(modelInfo: ModelStatus): string {
    return modelInfo?.loaded ? 'Cargado' : 'No entrenado';
  }
}
