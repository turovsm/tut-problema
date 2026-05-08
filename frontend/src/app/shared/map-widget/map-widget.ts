import { Component, inject, OnInit, ViewEncapsulation } from '@angular/core';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatSelectModule} from '@angular/material/select';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import * as L from 'leaflet';
import { CommonModule } from '@angular/common';
import { MapWidgetApiService } from './map-widget-api.service';

interface Complaint {
  id: number;
  title: string;
  type: string;
  district: string;
  lat: number;
  lng: number;
}

@Component({
  selector: 'app-dashboard',
  templateUrl: './map-widget.html',
  styleUrls: ['./map-widget.less'],
  encapsulation: ViewEncapsulation.None,
  imports:[ MatCardModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule, CommonModule]
})
export class MapWidget implements OnInit {
  map!: L.Map;
  complaints: Complaint[] = [];
  filteredComplaints: Complaint[] = [];

  types = ['Снег', 'Ямы', 'Освещение'];
  districts = ['Центр', 'Север', 'Юг', 'Восток', 'Запад'];

  selectedType = '';
  selectedDistrict = '';
  selectedPointMarker?: L.Marker;
  selectedLat?: number;
  selectedLng?: number;
  districtsLayer?: L.GeoJSON;
  private readonly apiService = inject(MapWidgetApiService);

  ngOnInit(): void {
    this.initMap();
    this.loadComplaints();
    this.loadReports();
    this.applyFilters();
  }

  initMap() {
    const permBounds: L.LatLngBoundsExpression = [
      [57.9, 56.0],  // юго-запад (southWest)
      [58.1, 56.5]   // северо-восток (northEast)
    ];

    this.map = L.map('map', {
      center: [58.0, 56.25],
      zoom: 12,
      maxBounds: permBounds,      // ограничение карты
      minZoom: 12,
      maxBoundsViscosity: 1.0    // "липкость" границ, чем ближе к 1, тем сильнее ограничение
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);
    
    this.addDistricts();
    this.map.on('click', (event: L.LeafletMouseEvent) => {
    this.setSelectedPoint(event.latlng.lat, event.latlng.lng);
    
});
  }

  loadComplaints() {
    // Пример данных, потом заменить API вызовом
    this.complaints = [
      { id: 1, title: 'Неубранный снег', type: 'Снег', district: 'Север', lat: 55.78, lng: 37.62 },
      { id: 2, title: 'Яма на дороге', type: 'Ямы', district: 'Центр', lat: 55.75, lng: 37.61 },
      { id: 3, title: 'Не работает фонарь', type: 'Освещение', district: 'Юг', lat: 55.73, lng: 37.63 }
    ];
  }

  applyFilters() {
    this.filteredComplaints = this.complaints.filter(c => 
      (this.selectedType ? c.type === this.selectedType : true) &&
      (this.selectedDistrict ? c.district === this.selectedDistrict : true)
    );
    this.updateMapMarkers();
  }

  updateMapMarkers() {
    this.map.eachLayer(layer => {
      if ((layer as any).options?.icon) {
        this.map.removeLayer(layer);
      }
    });

    this.filteredComplaints.forEach(c => {
      L.marker([c.lat, c.lng])
        .addTo(this.map)
        .bindPopup(`<b>${c.title}</b><br>${c.type}, ${c.district}`);
    });
  }

  createComplaint() {
    alert('Переход на форму создания заявки');
    // Можно добавить маршрутизацию: this.router.navigate(['/user/complaint/new'])
  }

  setSelectedPoint(lat: number, lng: number) {
    this.selectedLat = lat;
    this.selectedLng = lng;

    if (this.selectedPointMarker) {
      this.selectedPointMarker.setLatLng([lat, lng]);
    } else {
      this.selectedPointMarker = L.marker([lat, lng], {
        draggable: true
      }).addTo(this.map);

      this.selectedPointMarker.on('dragend', () => {
        const position = this.selectedPointMarker!.getLatLng();
        this.selectedLat = position.lat;
        this.selectedLng = position.lng;
      });
    }

    this.selectedPointMarker.bindPopup(
      `Выбранная точка:<br>${lat.toFixed(6)}, ${lng.toFixed(6)}`
    ).openPopup();
  }

  addDistricts() {
    fetch('assets/districts_perm.geojson')
      .then(res => res.json())
      .then(data => {
        this.districtsLayer = L.geoJSON(data, {
          style: {
            color: '#2563eb',       // цвет границы
            weight: 2,              // толщина линии
            fillColor: '#3b82f6',   // заливка
            fillOpacity: 0.15       // прозрачность заливки
          },
          onEachFeature: (feature, layer) => {
            if (feature.properties && feature.properties.name) {
              layer.bindPopup(feature.properties.name);
            }
          }
        }).addTo(this.map);

        // Ограничим карту границами города
        const cityBounds = this.districtsLayer.getBounds();
        this.map.setMaxBounds(cityBounds);
        this.map.fitBounds(cityBounds);
      });
  }

  private loadReports(): void {
    this.apiService.getNearbyReports().subscribe(reports => {
      if (!reports) {
        return;
      }
      reports.forEach(report => {
        const [lng, lat] = report.location.coordinates;
        const marker = L.marker([lat, lng]).addTo(this.map);
        marker.bindPopup(`
          <b>${report.title}</b><br>
          ${report.description}<br>
          Статус: ${report.status}
        `);
      });
    });
  }
}