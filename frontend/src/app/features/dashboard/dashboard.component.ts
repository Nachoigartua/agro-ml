import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Subscription } from 'rxjs';
import { debounceTime, finalize } from 'rxjs/operators';
import { ApiService } from '@core/services/api.service';
import { PdfDownloadService } from '@core/services/pdf-download.service';
import {
  SiembraHistoryFilters,
  SiembraHistoryItem,
} from '@shared/models/recommendations.model';
import {
  CAMPANAS_DISPONIBLES,
  CULTIVOS_DISPONIBLES,
  LOTES_DISPONIBLES,
  LoteOption,
} from '@shared/constants/farm.constants';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  readonly serverFiltersForm: FormGroup;
  readonly localSearchControl = new FormControl<string>('', { nonNullable: true });

  availableLotes: LoteOption[] = [];
  availableCultivos: string[] = [];
  availableCampanas: string[] = [];

  isLoading = true;
  error: string | null = null;
  totalHistory = 0;
  historyItems: SiembraHistoryItem[] = [];
  
  downloadingPdfId: string | null = null;

  private allHistoryItems: SiembraHistoryItem[] = [];
  private filteredHistoryItems: SiembraHistoryItem[] = [];
  private lastAppliedFilters = '{}';
  private activeRequestSubscription: Subscription | null = null;
  private readonly subscriptions = new Subscription();

  private readonly loteLabelMap = new Map<string, string>();

  constructor(
    private readonly apiService: ApiService,
    private readonly formBuilder: FormBuilder,
    private readonly pdfDownloadService: PdfDownloadService
  ) {
    this.serverFiltersForm = this.formBuilder.group({
      lote_id: [''],
      cultivo: [''],
      campana: [''],
    });

    this.bootstrapStaticOptions();
  }

  ngOnInit(): void {
    this.setupFilterSubscriptions();
    this.loadDashboardData();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.activeRequestSubscription?.unsubscribe();
  }

  loadDashboardData(): void {
    this.isLoading = true;
    this.error = null;
    const filters = this.normalizeFilterPayload(this.serverFiltersForm.value);
    this.lastAppliedFilters = JSON.stringify(filters);

    this.activeRequestSubscription?.unsubscribe();

    const requestSub = this.apiService.getSiembraHistory(filters).subscribe({
      next: (response) => {
        this.totalHistory = response.total;
        this.allHistoryItems = response.items;
        this.deriveFilterOptions(response.items);
        this.applyLocalFilters();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading siembra history:', err);
        this.allHistoryItems = [];
        this.filteredHistoryItems = [];
        this.historyItems = [];
        this.totalHistory = 0;
        this.error = 'No se pudo cargar el historial de recomendaciones';
        this.bootstrapStaticOptions();
        this.isLoading = false;
      }
    });

    this.activeRequestSubscription = requestSub;
    this.subscriptions.add(requestSub);
  }

  resolveConfidence(item: SiembraHistoryItem): number | null {
    const { nivel_confianza, recomendacion_principal } = item;
    if (typeof nivel_confianza === 'number') {
      return nivel_confianza;
    }

    return typeof recomendacion_principal?.confianza === 'number'
      ? recomendacion_principal.confianza
      : null;
  }

  shortId(value?: string): string {
    if (!value) {
      return '—';
    }

    const [prefix] = value.split('-');
    return prefix ? prefix.toUpperCase() : value.toUpperCase();
  }

  formatRecommendationDate(value?: string): string {
    if (!value) {
      return '—';
    }

    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return new Intl.DateTimeFormat('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }).format(parsed);
    }

    const match = /^(\d{2})-(\d{2})-(\d{4})$/.exec(value);
    if (match) {
      const [, day, month, year] = match;
      return `${day}/${month}/${year}`;
    }

    return value;
  }

  get filteredCount(): number {
    return this.filteredHistoryItems.length;
  }

  get hasServerResults(): boolean {
    return this.allHistoryItems.length > 0;
  }

  get isLocalSearchActive(): boolean {
    return this.localSearchControl.value.trim().length > 0;
  }

  get totalSummaryText(): string {
    if (this.totalHistory === 0) {
      return 'Sin recomendaciones registradas';
    }

    if (this.totalHistory === 1) {
      return '1 recomendación encontrada';
    }

    return `${this.totalHistory} recomendaciones encontradas`;
  }

  private setupFilterSubscriptions(): void {
    const filterChangesSub = this.serverFiltersForm.valueChanges
      .pipe(debounceTime(300))
      .subscribe(() => {
        const filters = this.normalizeFilterPayload(this.serverFiltersForm.value);
        const serialized = JSON.stringify(filters);
        if (serialized !== this.lastAppliedFilters) {
          this.loadDashboardData();
        }
      });

    const searchChangesSub = this.localSearchControl.valueChanges
      .pipe(debounceTime(200))
      .subscribe(() => this.applyLocalFilters());

    this.subscriptions.add(filterChangesSub);
    this.subscriptions.add(searchChangesSub);
  }

  private normalizeFilterPayload(
    values: Partial<SiembraHistoryFilters>
  ): SiembraHistoryFilters {
    const normalized: SiembraHistoryFilters = {};

    Object.entries(values ?? {}).forEach(([key, value]) => {
      if (typeof value === 'string' && value.trim().length > 0) {
        normalized[key as keyof SiembraHistoryFilters] = value.trim();
      }
    });

    return normalized;
  }

  private deriveFilterOptions(items: SiembraHistoryItem[]): void {
    const loteMap = new Map<string, LoteOption>(
      LOTES_DISPONIBLES.map((lote) => [lote.value, { ...lote }])
    );
    const cultivos = new Set<string>(CULTIVOS_DISPONIBLES);
    const campanas = new Set<string>(CAMPANAS_DISPONIBLES);

    LOTES_DISPONIBLES.forEach((lote) => {
      this.loteLabelMap.set(lote.value, lote.label);
    });

    items.forEach((item) => {
      if (item.lote_id) {
        if (!loteMap.has(item.lote_id)) {
          const label = this.deriveLoteLabel(item.lote_id);
          loteMap.set(item.lote_id, { label, value: item.lote_id });
        }

        this.loteLabelMap.set(item.lote_id, loteMap.get(item.lote_id)!.label);
      }

      if (item.cultivo) {
        cultivos.add(item.cultivo);
      }

      const campanaEntrada = item.datos_entrada
        ? (item.datos_entrada['campana'] as string | undefined)
        : undefined;
      const campana = item.campana ?? campanaEntrada;
      if (campana) {
        campanas.add(campana);
      }
    });

    const baseLoteIds = new Set(LOTES_DISPONIBLES.map((lote) => lote.value));
    const orderedBaseLotes = LOTES_DISPONIBLES.map((lote) => loteMap.get(lote.value)).filter((lote): lote is LoteOption => Boolean(lote));
    const extraLotes = Array.from(loteMap.values()).filter((lote) => !baseLoteIds.has(lote.value)).sort((a, b) => a.label.localeCompare(b.label));
    this.availableLotes = [...orderedBaseLotes, ...extraLotes];

    const baseCultivos = [...CULTIVOS_DISPONIBLES];
    const baseCultivoSet = new Set(baseCultivos);
    const extraCultivos = Array.from(cultivos).filter(
      (cultivo) => !baseCultivoSet.has(cultivo)
    );
    this.availableCultivos = [
      ...baseCultivos,
      ...extraCultivos.sort((a, b) => a.localeCompare(b)),
    ];
    const baseCampanas = [...CAMPANAS_DISPONIBLES];
    const baseCampañaSet = new Set(baseCampanas);
    const extraCampanas = Array.from(campanas).filter(
      (campana) => !baseCampañaSet.has(campana)
    );
    this.availableCampanas = [
      ...baseCampanas,
      ...extraCampanas.sort((a, b) => a.localeCompare(b)),
    ];
  }

  private applyLocalFilters(): void {
    const searchTerm = this.localSearchControl.value
      ? this.localSearchControl.value.trim().toLowerCase()
      : '';

    const filtered = searchTerm
      ? this.allHistoryItems.filter((item) => this.matchesSearch(item, searchTerm))
      : [...this.allHistoryItems];

    this.filteredHistoryItems = [...filtered];
    this.historyItems = [...filtered];
  }

  private matchesSearch(item: SiembraHistoryItem, query: string): boolean {
    if (!query) {
      return true;
    }

    const values: string[] = [];

    if (item.cultivo) values.push(item.cultivo);
    if (item.campana) values.push(item.campana);
    if (item.lote_id) {
      const loteLabel = this.getLoteLabel(item.lote_id);
      values.push(item.lote_id);
      if (loteLabel !== '—') {
        values.push(loteLabel);
      }
      const loteShort = this.shortId(item.lote_id);
      if (loteShort !== '—') {
        values.push(loteShort);
      }
    }
    if (item.modelo_version) values.push(item.modelo_version);
    if (item.recomendacion_principal?.fecha_optima) {
      values.push(item.recomendacion_principal.fecha_optima);
    }
    item.recomendacion_principal?.ventana?.forEach((valor) => {
      if (valor) {
        values.push(valor);
      }
    });

    if (item.fecha_creacion) {
      values.push(item.fecha_creacion);
      const fechaFormateada = this.formatRecommendationDate(item.fecha_creacion);
      if (fechaFormateada !== '—') {
        values.push(fechaFormateada);
      }
    }

    const datosEntrada = item.datos_entrada ?? {};
    Object.values(datosEntrada).forEach((value) => {
      if (value === null || value === undefined) {
        return;
      }

      if (typeof value === 'string' || typeof value === 'number') {
        values.push(String(value));
      }
    });

    return values.some((value) => value.toLowerCase().includes(query));
  }

  getLoteLabel(loteId?: string): string {
    if (!loteId) {
      return '—';
    }

    return this.loteLabelMap.get(loteId) ?? this.shortId(loteId);
  }

  private bootstrapStaticOptions(): void {
    this.loteLabelMap.clear();
    this.availableLotes = LOTES_DISPONIBLES.map((lote) => {
      this.loteLabelMap.set(lote.value, lote.label);
      return { ...lote };
    });
    this.availableCultivos = [...CULTIVOS_DISPONIBLES];
    this.availableCampanas = [...CAMPANAS_DISPONIBLES];
  }

  private deriveLoteLabel(loteId: string): string {
    return this.loteLabelMap.get(loteId) ?? this.shortId(loteId);
  }

  /**
   * Descarga el PDF de una recomendación específica
   * @param item Elemento del historial
   */
  downloadRecommendationPdf(item: SiembraHistoryItem): void {
    if (!item.id) {
      console.warn('ID de recomendación no disponible');
      return;
    }

    this.downloadingPdfId = item.id;

    this.pdfDownloadService
      .downloadRecommendationPdf(item.id, item.cultivo)
      .pipe(finalize(() => (this.downloadingPdfId = null)))
      .subscribe({
        next: (blob: Blob) => {
          const cultivo = item.cultivo || 'desconocido';
          const filename = `recomendacion_${cultivo}_${new Date().getTime()}.pdf`;
          this.pdfDownloadService.triggerDownload(blob, filename);
        },
        error: (err: any) => {
          console.error('Error al descargar PDF:', err);
          alert('No se pudo descargar el PDF. Por favor, intenta nuevamente.');
        }
      });
  }

  /**
   * Verifica si se está descargando un PDF específico
   * @param id ID del elemento
   */
  isDownloadingPdf(id: string): boolean {
    return this.downloadingPdfId === id;
  }
}
