import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

type Lote = { id: string; nombre: string; latitud: number; longitud: number; hectareas: number; cultivo_id?: string|null; };
type Campana = { id: string; nombre: string; };
type Clima = { temp_media: number; precip: number; humedad: number; viento: number; radiacion: number; };
type VariedadRec = { variedad: string; razon: string; };
type SiembraRec = { densidad_plantas_ha: number; profundidad_cm: number; observaciones?: string; };
type FertPlan = { n_kg_ha: number; p_kg_ha: number; k_kg_ha: number; observaciones?: string; };

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, HttpClientModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  private http = inject(HttpClient);

  title = 'Agro ML';
  lotes = signal<Lote[]>([]);
  campanas = signal<Campana[]>([]);
  selectedLoteId = signal<string>('');
  selectedCampanaId = signal<string>('');

  clima = signal<Clima|null>(null);
  variedades = signal<VariedadRec[]|null>(null);
  siembra = signal<SiembraRec|null>(null);
  fert = signal<FertPlan|null>(null);
  loading = signal<boolean>(false);
  error = signal<string|null>(null);

  ngOnInit() {
    this.http.get<Campana[]>('/api/v1/catalogo/campanas').subscribe({
      next: (d) => this.campanas.set(d),
      error: () => this.error.set('No se pudo cargar campañas')
    });
    this.http.get<Lote[]>('/api/v1/catalogo/lotes').subscribe({
      next: (d) => { this.lotes.set(d); if (d.length) this.selectedLoteId.set(d[0].id); },
      error: () => this.error.set('No se pudo cargar lotes')
    });
  }

  generar() {
    this.error.set(null);
    this.loading.set(true);
    const lote = this.lotes().find(l => l.id === this.selectedLoteId());
    if (!lote) { this.error.set('Elegí un lote.'); this.loading.set(false); return; }

    const clima$ = this.http.post<Clima>('/api/v1/predicciones/clima', { coords: { latitud: lote.latitud, longitud: lote.longitud }, dias: 7 });
    const var$ = this.http.post<VariedadRec[]>('/api/v1/recomendaciones/variedades', { lote_id: lote.id });
    const sie$ = this.http.post<SiembraRec>('/api/v1/recomendaciones/siembra', { lote_id: lote.id });
    const fer$ = this.http.post<FertPlan>('/api/v1/optimizacion/fertilizacion', { lote_id: lote.id });

    clima$.subscribe({ next: (c) => { this.clima.set(c); }, error: () => { this.clima.set(null); } });
    var$.subscribe({ next: (v) => this.variedades.set(v), error: () => this.variedades.set(null) });
    sie$.subscribe({ next: (s) => this.siembra.set(s), error: () => this.siembra.set(null) });
    fer$.subscribe({ next: (f) => this.fert.set(f), error: () => this.fert.set(null) });

    this.loading.set(false);
  }
}
