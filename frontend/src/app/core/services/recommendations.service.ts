import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environments/environment';
import { SiembraRecommendationRequest, SiembraRecommendationResponse } from '@shared/models/recommendations.model';

@Injectable({
  providedIn: 'root'
})
export class RecommendationsService {
  private readonly baseUrl = `${environment.apiBaseUrl}/api/v1/recomendaciones`;

  constructor(private readonly http: HttpClient) {}

  generateSiembraRecommendation(
    payload: SiembraRecommendationRequest
  ): Observable<SiembraRecommendationResponse> {
    return this.http.post<SiembraRecommendationResponse>(`${this.baseUrl}/siembra`, payload);
  }
}
