import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '@environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Predicción de siembra
  predictSiembra(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/predict/siembra`, data)
      .pipe(catchError(this.handleError));
  }

  // Predicción de variedades
  predictVariedades(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/predict/variedades`, data)
      .pipe(catchError(this.handleError));
  }

  // Predicción de rendimiento
  predictRendimiento(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/predict/rendimiento`, data)
      .pipe(catchError(this.handleError));
  }

  // Predicción de fertilización
  predictFertilizacion(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/predict/fertilizacion`, data)
      .pipe(catchError(this.handleError));
  }

  // Predicción climática
  predictClima(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/predict/clima`, data)
      .pipe(catchError(this.handleError));
  }

  // Predicción de cosecha
  predictCosecha(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/predict/cosecha`, data)
      .pipe(catchError(this.handleError));
  }

  // Entrenar modelo
  trainModel(modelName: string, data: any = {}): Observable<any> {
    return this.http.post(`${this.apiUrl}/ml/train/${modelName}`, data)
      .pipe(catchError(this.handleError));
  }

  // Estado de modelos
  getModelsStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}/ml/models/status`)
      .pipe(catchError(this.handleError));
  }

  // Health check
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`)
      .pipe(catchError(this.handleError));
  }

  // Mock endpoints (solo en desarrollo)
  getLotes(clienteId?: string): Observable<any> {
    const url = clienteId 
      ? `${this.apiUrl}/mock/lotes?cliente_id=${clienteId}`
      : `${this.apiUrl}/mock/lotes`;
    return this.http.get(url)
      .pipe(catchError(this.handleError));
  }

  getLote(loteId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/mock/lotes/${loteId}`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: any) {
    console.error('API Error:', error);
    return throwError(() => new Error(error.message || 'Error en la API'));
  }
}