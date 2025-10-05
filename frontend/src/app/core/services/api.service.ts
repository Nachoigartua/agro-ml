import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '@environments/environment';
import { Lote, ModelStatus, HealthStatusResponse, ModelsDashboardState } from '@shared/models/recommendations.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiBaseUrl;

  constructor(private readonly http: HttpClient) {}

  healthCheck(): Observable<HealthStatusResponse> {
    return this.http
      .get<HealthStatusResponse>(`${this.baseUrl}/health`)
      .pipe(catchError(this.handleError));
  }

  getModelsStatus(): Observable<ModelsDashboardState> {
    return this.http
      .get<ModelsDashboardState>(`${this.baseUrl}/api/v1/modelos/estado`)
      .pipe(catchError(this.handleError));
  }

  triggerModelTraining(
    modelName: string,
    payload: Record<string, unknown> = {}
  ): Observable<Record<string, unknown>> {
    return this.http
      .post<Record<string, unknown>>(`${this.baseUrl}/api/v1/modelos/${modelName}/entrenar`, payload)
      .pipe(catchError(this.handleError));
  }

  getLotes(clienteId?: string): Observable<Lote[]> {
    const url = clienteId
      ? `${this.baseUrl}/mock/lotes?cliente_id=${clienteId}`
      : `${this.baseUrl}/mock/lotes`;

    return this.http
      .get<Lote[]>(url)
      .pipe(catchError(this.handleError));
  }

  getLote(loteId: string): Observable<Lote> {
    return this.http
      .get<Lote>(`${this.baseUrl}/mock/lotes/${loteId}`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: any) {
    console.error('API Error:', error);
    return throwError(() => new Error(error?.message ?? 'Error en la API'));
  }
}
