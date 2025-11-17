import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from '@angular/forms';
import { Subscription } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { ApiService } from '@core/services/api.service';
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
import { MiniMapComponent } from './mini-map/mini-map.component';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  @ViewChild(MiniMapComponent) miniMap?: MiniMapComponent;
  readonly serverFiltersForm: FormGroup;
  readonly localSearchControl = new FormControl<string>('', { nonNullable: true });

  availableLotes: LoteOption[] = [];
  availableCultivos: string[] = [];
  availableCampanas: string[] = [];

  isLoading = true;
  error: string | null = null;
  totalHistory = 0;
  historyItems: SiembraHistoryItem[] = [];

  private allHistoryItems: SiembraHistoryItem[] = [];
  private filteredHistoryItems: SiembraHistoryItem[] = [];
  private lastAppliedFilters = '{}';
  private activeRequestSubscription: Subscription | null = null;
  private readonly subscriptions = new Subscription();

  private readonly loteLabelMap = new Map<string, string>();
  private readonly selectedLotes = new Set<string>();

  constructor(
    private readonly apiService: ApiService,
    private readonly formBuilder: FormBuilder
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
      .subscribe((raw) => {
        // Sincroniza selección de UI -> mapa
        const rawLote = (raw as any)?.lote_id as string | string[] | undefined;
        const ids = Array.isArray(rawLote)
          ? rawLote.filter((v) => !!v)
          : (rawLote ? [rawLote] : []);
        if (this.miniMap) {
          this.miniMap.setSelection(ids);
        }
        this.selectedLotes.clear();
        ids.forEach((id) => this.selectedLotes.add(id));
        this.applyLocalFilters();

        // Decide si hace request al backend
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
      if (Array.isArray(value)) {
        // Si múltiples lotes, no enviamos a backend. Si 1, lo enviamos como string
        if (value.length === 1 && typeof value[0] === 'string' && value[0].trim().length > 0) {
          (normalized as any)[key] = value[0].trim();
        }
        return;
      }

      if (typeof value === 'string' && value.trim().length > 0) {
        (normalized as any)[key] = value.trim();
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

    const hasSelection = this.selectedLotes.size > 0;

    const filtered = this.allHistoryItems.filter((item) => {
      const matchesSearch = !searchTerm || this.matchesSearch(item, searchTerm);
      const matchesSelection = !hasSelection || (item.lote_id && this.selectedLotes.has(item.lote_id));
      return matchesSearch && matchesSelection;
    });

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

    const display = this.loteLabelMap.get(loteId) ?? this.shortId(loteId);
    return display === '—' ? display : `Lote ${display}`;
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

  onSelectedLotesChange(ids: string[]): void {
    this.selectedLotes.clear();
    ids.forEach((id) => this.selectedLotes.add(id));
    // Reflejar selección en el select (sin disparar requests)
    const control = this.serverFiltersForm.get('lote_id');
    if (control) {
      // Dropdown simple: si hay 0 -> '', 1 -> id, >1 -> '' (mostrar 'Todos')
      control.setValue(ids.length === 1 ? ids[0] : '', { emitEvent: false });
    }

    // Si 0 o 1 seleccionado, podemos pegar al backend; si >1, filtramos local
    if (ids.length <= 1) {
      const filters = this.normalizeFilterPayload(this.serverFiltersForm.value);
      const serialized = JSON.stringify(filters);
      if (serialized !== this.lastAppliedFilters) {
        this.loadDashboardData();
        return;
      }
      this.applyLocalFilters();
      return;
    }

    // >1 seleccionado: cargar todo el historial (sin lote_id) y luego filtrar localmente
    this.loadDashboardData();
  }

  // Maneja cambios normales del dropdown; la lógica principal ya está en valueChanges del form.
  onLoteDropdownChange(event: Event): void {
    // No hacemos nada aquí; el valueChanges del form se encarga.
  }

  // Caso especial: si ya está en '' (Todos), seleccionar otra vez no dispara valueChanges.
  // Detectamos el click y, si corresponde, limpiamos selección del mapa y filtros locales.
  onLoteDropdownClick(event: Event): void {
    const current = (event.target as HTMLSelectElement)?.value ?? '';
    if (current === '' && this.selectedLotes.size > 0) {
      this.miniMap?.clearSelection();
      this.selectedLotes.clear();
      this.applyLocalFilters();

      const filters = this.normalizeFilterPayload(this.serverFiltersForm.value);
      const serialized = JSON.stringify(filters);
      if (serialized !== this.lastAppliedFilters) {
        this.loadDashboardData();
      }
    }
  }
}
