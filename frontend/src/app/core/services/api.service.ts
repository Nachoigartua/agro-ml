import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '@environments/environment';
import { HealthStatusResponse } from '@shared/models/recommendations.model';

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

  private handleError(error: any) {
    console.error('API Error:', error);
    return throwError(() => new Error(error?.message ?? 'Error en la API'));
  }
}
