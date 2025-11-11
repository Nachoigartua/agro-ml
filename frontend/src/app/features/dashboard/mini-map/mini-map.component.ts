import { Component, AfterViewInit, OnDestroy, Output, EventEmitter } from '@angular/core';
import { Subscription } from 'rxjs';
import * as L from 'leaflet';
import { ApiService } from '@core/services/api.service';
import { LoteItem } from '@shared/models/lotes.model';

@Component({
  selector: 'app-mini-map',
  templateUrl: './mini-map.component.html',
  styleUrls: ['./mini-map.component.scss']
})
export class MiniMapComponent implements AfterViewInit, OnDestroy {
  private map: L.Map | null = null;
  private subscriptions = new Subscription();
  private markersById = new Map<string, L.CircleMarker>();
  private selected = new Set<string>();

  @Output() selectedLotesChange = new EventEmitter<string[]>();

  constructor(private readonly api: ApiService) {}

  ngAfterViewInit(): void {
    this.initMap();
    const sub = this.api.getLotes().subscribe({
      next: (resp) => this.renderLotes(resp.items),
      error: (err) => {
        console.error('No se pudieron cargar los lotes para el mapa', err);
      }
    });
    this.subscriptions.add(sub);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap(): void {
    const argentinaCenter: L.LatLngExpression = [-38.4161, -63.6167];
    this.map = L.map('mini-map-container', {
      center: argentinaCenter,
      zoom: 4,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);
  }

  private renderLotes(lotes: LoteItem[]): void {
    if (!this.map || !lotes?.length) {
      return;
    }

    const bounds = L.latLngBounds([]);
    lotes.forEach((lote) => {
      const latLng = L.latLng(lote.latitud, lote.longitud);
      bounds.extend(latLng);

      const marker = L.circleMarker(latLng, { ...this.style(false), radius: 6 } as L.CircleMarkerOptions)
        .bindTooltip(`${lote.nombre}`, { permanent: false, direction: 'top' })
        .addTo(this.map!);

      marker.on('click', () => this.toggleSelection(lote.lote_id));
      this.markersById.set(lote.lote_id, marker);
    });

    if (bounds.isValid()) {
      this.map.fitBounds(bounds.pad(0.2));
    }
  }

  private toggleSelection(loteId: string): void {
    if (this.selected.has(loteId)) {
      this.selected.delete(loteId);
    } else {
      this.selected.add(loteId);
    }
    this.updateMarkerStyles();
    this.selectedLotesChange.emit(Array.from(this.selected));
  }

  private updateMarkerStyles(): void {
    this.markersById.forEach((marker, id) => {
      const selected = this.selected.has(id);
      marker.setStyle(this.style(selected));
      marker.setRadius(selected ? 8 : 6);
      if (selected) {
        marker.bringToFront();
      } else {
        marker.bringToBack();
      }
    });
  }

  private style(selected: boolean): L.PathOptions {
    return selected
      ? {
          color: '#1976d2',
          weight: 3,
          fillColor: '#64b5f6',
          fillOpacity: 0.9,
        }
      : {
          color: '#2e7d32',
          weight: 2,
          fillColor: '#8bc34a',
          fillOpacity: 0.8,
        };
  }

  clearSelection(): void {
    this.selected.clear();
    this.updateMarkerStyles();
    this.selectedLotesChange.emit([]);
  }

  setSelection(ids: string[]): void {
    this.selected.clear();
    ids.forEach((id) => this.selected.add(id));
    this.updateMarkerStyles();
    // No emitimos evento aquí para evitar loops; solo actualiza visualmente
  }
}
