import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

/**
 * Servicio para manejar descargas de PDF de recomendaciones
 */
@Injectable({
  providedIn: 'root'
})
export class PdfDownloadService {
  private readonly apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  /**
   * Descarga el PDF de una recomendación específica
   * @param prediccionId ID de la predicción/recomendación
   * @param cultivo Cultivo (opcional, para el nombre del archivo)
   * @returns Observable que emite el Blob del PDF
   */
  downloadRecommendationPdf(
    prediccionId: string,
    cultivo?: string
  ): Observable<Blob> {
    const url = `${this.apiUrl}/recomendaciones/siembra/${prediccionId}/pdf`;
    
    return this.http.post(
      url,
      {},
      {
        responseType: 'blob'
      }
    );
  }

  /**
   * Dispara la descarga del archivo PDF en el navegador
   * @param blob Blob del PDF
   * @param filename Nombre del archivo
   */
  triggerDownload(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}
