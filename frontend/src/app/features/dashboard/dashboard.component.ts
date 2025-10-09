import { Component, OnInit } from '@angular/core';
import { ApiService } from '@core/services/api.service';
import { HealthStatusResponse } from '@shared/models/recommendations.model';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
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
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading health status:', err);
        this.healthStatus = null;
        this.error = 'Error al cargar el estado del servicio';
        this.isLoading = false;
      }
    });
  }

}
