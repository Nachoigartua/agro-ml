import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Lote {
  id: string;
  cliente_id: string;
  nombre?: string;
  superficie_ha?: number;
  geom_wkt?: string;
}

export interface SiembraRequest {
  lote_id: string;
  cliente_id: string;
  cultivo: 'trigo' | 'soja' | 'maiz' | 'cebada';
}

export interface Recomendacion {
  recomendacion_principal: string;
  fecha_optima?: string;
  ventana_inicio?: string;
  ventana_fin?: string;
  confianza: number;
  riesgos?: string;
  alternativas: string[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = (window as any).__ML_BACKEND__ || 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private headers(): HttpHeaders {
    const token = localStorage.getItem('auth_token') || '';
    return new HttpHeaders(token ? { Authorization: `Bearer ${token}` } : {});
  }

  lotes(clienteId: string): Observable<Lote[]> {
    const params = new HttpParams().set('cliente_id', clienteId);
    return this.http.get<Lote[]>(`${this.base}/api/v1/lotes`, { params, headers: this.headers() });
    // Conforme EF: selección de lotes, vista por lote, etc.
  }

  recoSiembra(req: SiembraRequest): Observable<Recomendacion> {
    return this.http.post<Recomendacion>(`${this.base}/api/v1/recomendaciones/siembra`, req, { headers: this.headers() });
  }
}
