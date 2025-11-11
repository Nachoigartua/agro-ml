import { Component, AfterViewInit, OnDestroy } from '@angular/core';
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

      L.circleMarker(latLng, {
        radius: 6,
        color: '#2e7d32',
        weight: 2,
        fillColor: '#8bc34a',
        fillOpacity: 0.8,
      })
        .bindTooltip(`${lote.nombre}`, { permanent: false, direction: 'top' })
        .addTo(this.map!);
    });

    if (bounds.isValid()) {
      this.map.fitBounds(bounds.pad(0.2));
    }
  }
}

