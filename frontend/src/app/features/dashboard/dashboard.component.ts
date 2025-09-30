import { Component, OnInit } from '@angular/core';
import { ApiService } from '@core/services/api.service';
import { ModelStatus } from '@shared/models/predictions.model';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  modelsStatus: any = null;
  isLoading = true;
  error: string | null = null;
  healthStatus: any = null;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.isLoading = true;
    this.error = null;

    // Cargar estado de salud
    this.apiService.healthCheck().subscribe({
      next: (data) => {
        this.healthStatus = data;
      },
      error: (err) => {
        console.error('Error loading health status:', err);
      }
    });

    // Cargar estado de modelos
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

  trainModel(modelName: string): void {
    if (confirm(`¿Desea entrenar el modelo ${modelName}? Esto puede tomar varios minutos.`)) {
      this.isLoading = true;
      
      this.apiService.trainModel(modelName, { force_retrain: true }).subscribe({
        next: (response) => {
          alert(`Modelo ${modelName} entrenado exitosamente`);
          this.loadDashboardData(); // Recargar estado
        },
        error: (err) => {
          alert(`Error al entrenar el modelo: ${err.message}`);
          this.isLoading = false;
        }
      });
    }
  }

  getModelsList(): string[] {
    if (!this.modelsStatus?.models) return [];
    return Object.keys(this.modelsStatus.models);
  }

  getModelInfo(modelName: string): any {
    return this.modelsStatus?.models[modelName] || {};
  }

  getModelStatusClass(modelInfo: any): string {
    return modelInfo.loaded ? 'status-loaded' : 'status-not-loaded';
  }

  getModelStatusText(modelInfo: any): string {
    return modelInfo.loaded ? 'Cargado' : 'No entrenado';
  }
}