import { Component, inject, OnInit, signal, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

import * as L from 'leaflet';

import { MapWidgetApiService } from './map-widget-api.service';
import {
  ComplaintFormComponent,
  ComplaintFormValue
} from '../complaint-form/complaint-form';

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
  standalone: true,
  templateUrl: './map-widget.html',
  styleUrls: ['./map-widget.less'],
  encapsulation: ViewEncapsulation.None,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    ComplaintFormComponent
  ]
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

  isComplaintFormOpen = signal(false);
  selectedAddress = signal('Адрес точки');

  // TODO: заменить на реальную проверку авторизации через AuthService
  isAuthorized = true;

  private readonly apiService = inject(MapWidgetApiService);

  ngOnInit(): void {
    this.initMap();
    this.loadReports();
    this.applyFilters();
    this.initUserLocationMarker();
  }

  initMap(): void {
    const permBounds: L.LatLngBoundsExpression = [
      [57.9, 56.0],
      [58.1, 56.5]
    ];

    this.map = L.map('map', {
      center: [58.0, 56.25],
      zoom: 12,
      maxBounds: permBounds,
      minZoom: 12,
      maxBoundsViscosity: 1.0
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.addDistricts();

    this.map.on('click', (event: L.LeafletMouseEvent) => {
      this.setSelectedPoint(event.latlng.lat, event.latlng.lng);
    });
  }

  applyFilters(): void {
    this.filteredComplaints = this.complaints.filter(c =>
      (this.selectedType ? c.type === this.selectedType : true) &&
      (this.selectedDistrict ? c.district === this.selectedDistrict : true)
    );

    this.updateMapMarkers();
  }

  updateMapMarkers(): void {
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

  createComplaint(): void {
  if (!this.isAuthorized) {
    alert('Чтобы сообщить о проблеме, необходимо авторизоваться');
    return;
  }

  if (this.selectedLat === undefined || this.selectedLng === undefined) {
    alert('Выберите точку на карте');
    return;
  }

  this.isComplaintFormOpen.set(true);
  this.selectedPointMarker?.closePopup();

  setTimeout(() => {
    this.map.invalidateSize();
  });
}

closeComplaintForm(): void {
  this.isComplaintFormOpen.set(false);

  setTimeout(() => {
    this.map.invalidateSize();
  });
}

  submitComplaint(value: ComplaintFormValue): void {
      const formData = new FormData();

      formData.append('title', value.title);
      formData.append('description', value.description ?? '');
      formData.append('issue_type', value.issue_type);

      formData.append('location_lng', String(value.location_lng));
      formData.append('location_lat', String(value.location_lat));

      formData.append('user_location_lng', String(value.location_lng));
      formData.append('user_location_lat', String(value.location_lat));

      value.files.forEach(file => {
        formData.append('files', file, file.name);
      });

      this.apiService.createComplaint(formData).subscribe({
        next: response => {
          if (response.status !== 'success') {
            alert(response.message || 'Не удалось создать жалобу');
            return;
          }

          alert('Жалоба успешно создана');
          this.closeComplaintForm();
          this.loadReports();
        },
        error: error => {
          console.error('Ошибка создания жалобы:', error);

          if (error.status === 400) {
            alert(error.error?.message || 'Проверьте данные жалобы');
            return;
          }

          if (error.status === 401) {
            alert('Необходимо авторизоваться');
            return;
          }

          if (error.status === 403) {
            alert("Необходимо подтвердить почту");
            return;
          }

          if (error.status === 409) {
            alert('Похожая жалоба уже существует. Можно проголосовать за неё.');
            return;
          }

          alert('Ошибка сервера при создании жалобы');
        }
      });
}

  private setSelectedPoint(lat: number, lng: number): void {
    this.selectedLat = lat;
    this.selectedLng = lng;
    this.loadAddressFromCoords(this.selectedLat, this.selectedLng);

    if (this.selectedPointMarker) {
      this.selectedPointMarker.setLatLng([lat, lng]);
    } else {

      const  pinIcon = L.icon({
          iconUrl: 'assets/pin.svg',
          iconSize: [40, 40],
          iconAnchor: [20, 37],
          popupAnchor:  [0, -40]
      });

      this.selectedPointMarker = L.marker([lat, lng], {
        draggable: true,
        icon: pinIcon,
      }).addTo(this.map);

      this.selectedPointMarker.on('dragend', () => {
        const position = this.selectedPointMarker!.getLatLng();
        this.selectedLat = position.lat;
        this.selectedLng = position.lng;
      });
    }

    const button = document.createElement('button');

    button.type = 'button';
    button.className = 'create-complaint-button';
    button.textContent = 'Сообщить о проблеме';

    button.addEventListener('click', event => {
      event.stopPropagation();
      event.preventDefault();
      this.createComplaint();
    });
    if (!this.isComplaintFormOpen()) {
      this.selectedPointMarker
        .bindPopup(button)
        .openPopup();
    }
  }

  private addDistricts(): void {
    fetch('assets/districts_perm.geojson')
      .then(res => res.json())
      .then(data => {
        this.districtsLayer = L.geoJSON(data, {
          style: {
            color: '#2563eb',
            weight: 2,
            fillColor: '#3b82f6',
            fillOpacity: 0.15
          }
        }).addTo(this.map);

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

  private loadAddressFromCoords(lat: number, lng: number) {
     this.selectedAddress.set('Определяем адрес...');

     this.apiService.loadAddress(lat, lng).subscribe({
      next: data => {
        this.selectedAddress.set(data.display_name || 'Адрес не найден');
      },
      error: () => {
        this.selectedAddress.set('Адрес не найден');
      }
    });
  }

  private initUserLocationMarker(): void {
    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        this.setSelectedPoint(lat, lng);

        this.map.setView([lat, lng], 15);
      },
      error => {
        console.warn('Пользователь не дал доступ к геолокации или произошла ошибка:', error);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  }
}