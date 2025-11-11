import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '@environments/environment';
import {
  HealthStatusResponse,
  SiembraHistoryFilters,
  SiembraHistoryResponse,
} from '@shared/models/recommendations.model';
import { LotesListResponse } from '@shared/models/lotes.model';

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

  getSiembraHistory(
    filters: SiembraHistoryFilters = {}
  ): Observable<SiembraHistoryResponse> {
    let params = new HttpParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params = params.set(key, value);
      }
    });

    return this.http
      .get<SiembraHistoryResponse>(
        `${this.baseUrl}/api/v1/recomendaciones/siembra/historial`,
        { params }
      )
      .pipe(catchError(this.handleError));
  }

  getLotes(): Observable<LotesListResponse> {
    return this.http
      .get<LotesListResponse>(`${this.baseUrl}/api/v1/lotes`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: any) {
    console.error('API Error:', error);
    return throwError(() => new Error(error?.message ?? 'Error en la API'));
  }
}
