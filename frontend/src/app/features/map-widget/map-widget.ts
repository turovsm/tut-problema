import {
  Component,
  inject,
  OnInit,
  signal,
  ViewEncapsulation,
} from '@angular/core';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

import * as L from 'leaflet';

import { MapWidgetApiService, Report } from './map-widget-api.service';
import {
  ComplaintFormComponent,
  ComplaintFormValue,
} from '../complaint-form/complaint-form';

import { IssueType, ISSUE_TYPE_LABELS } from '../../core/models/issue-type';
import { AuthService } from '../../core/auth/auth.service';
import { REPORT_STATUS_OPTIONS, ReportStatus } from '../../core/models/report.models';

interface Complaint {
  id: string;
  title: string;
  type: IssueType;
  district: string;
  lat: number;
  lng: number;
  status: 'pending' | 'confirmed' | 'dismissed' | 'resolved';
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './map-widget.html',
  styleUrls: ['./map-widget.less'],
  encapsulation: ViewEncapsulation.None,
  imports: [
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    ComplaintFormComponent,
  ],
})
export class MapWidget implements OnInit {
  map!: L.Map;
  private readonly authService = inject(AuthService);
  types = Object.keys(ISSUE_TYPE_LABELS) as IssueType[];

  complaints: Complaint[] = [];
  filteredComplaints: Complaint[] = [];

  statuses: ReportStatus[] = ['pending', 'confirmed', 'dismissed', 'resolved'];

  typeLabels = ISSUE_TYPE_LABELS;
  statusLabels= REPORT_STATUS_OPTIONS;

  selectedType: IssueType | '' = '';
  selectedStatus: 'pending' | 'confirmed' | 'dismissed' | 'resolved' | '' = '';

  selectedPointMarker?: L.Marker;
  selectedLat?: number;
  selectedLng?: number;

  districtsLayer?: L.GeoJSON;

  isComplaintFormOpen = signal(false);
  selectedAddress = signal('Адрес точки');

  private readonly apiService = inject(MapWidgetApiService);

  private readonly complaintMarkersLayer = L.layerGroup();

  private readonly issueTypeColors: Record<IssueType, string> = {
    snow: '#60a5fa',
    pothole: '#f97316',
    road_obstruction: '#ef4444',
    flooding: '#06b6d4',
    broken_streetlight: '#facc15',
    broken_sidewalk: '#a855f7',
    water_leak: '#0ea5e9',
    sewer_overflow: '#64748b',
    illegal_dumping: '#22c55e',
    other: '#9ca3af',
  };

  ngOnInit(): void {
    this.initMap();
    this.loadReports();
    this.applyFilters();
    this.initUserLocationMarker();
  }

  initMap(): void {
    const permBounds: L.LatLngBoundsExpression = [
      [57.9, 56.0],
      [58.1, 56.5],
    ];

    this.map = L.map('map', {
      center: [58.0, 56.25],
      zoom: 12,
      maxBounds: permBounds,
      minZoom: 12,
      maxBoundsViscosity: 1.0,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(this.map);

    this.complaintMarkersLayer.addTo(this.map);

    this.addDistricts();

    this.map.on('click', (event: L.LeafletMouseEvent) => {
      this.setSelectedPoint(event.latlng.lat, event.latlng.lng);
    });
  }

  applyFilters(): void {
    this.filteredComplaints = this.complaints.filter(
      (c) =>
        (this.selectedType ? c.type === this.selectedType : true) &&
        (this.selectedStatus ? c.status === this.selectedStatus : true),
    );

    this.updateMapMarkers();
  }

  updateMapMarkers(): void {
    this.complaintMarkersLayer.clearLayers();

    this.filteredComplaints.forEach((c) => {
      const marker = this.createComplaintCircleMarker(c.lat, c.lng, c.type);

      marker
        .bindPopup(
          `
          <div class="complaint-popup">
            <b>${c.title}</b><br>
            Тип: ${this.getIssueLabel(c.type)}<br>
            Район: ${c.district || 'не указан'}<br><br>
            <a href="/reports/${c.id}" class="popup-details-link">
              Подробнее
            </a>
          </div>
        `,
        )
        .addTo(this.complaintMarkersLayer);
    });
  }

  createComplaint(): void {
    if (!this.authService.isAuthenticated()) {
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

    value.files.forEach((file) => {
      formData.append('files', file, file.name);
    });

    this.apiService.createComplaint(formData).subscribe({
      next: (response) => {
        if (response.status !== 'success') {
          alert(response.message || 'Не удалось создать жалобу');
          return;
        }

        alert('Жалоба успешно создана');
        this.closeComplaintForm();
        this.loadReports();
      },
      error: (error) => {
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
          alert('Необходимо подтвердить почту');
          return;
        }

        if (error.status === 409) {
          alert('Похожая жалоба уже существует. Можно проголосовать за неё.');
          return;
        }

        alert('Ошибка сервера при создании жалобы');
      },
    });
  }

  getIssueLabel(type: IssueType | string): string {
    return ISSUE_TYPE_LABELS[type as IssueType] ?? type;
  }

  private getIssueColor(type: IssueType | string): string {
    return (
      this.issueTypeColors[type as IssueType] ?? this.issueTypeColors['other']
    );
  }

  private createComplaintCircleMarker(
    lat: number,
    lng: number,
    type: IssueType | string,
  ): L.CircleMarker {
    const color = this.getIssueColor(type);

    return L.circleMarker([lat, lng], {
      radius: 9,
      color,
      fillColor: color,
      fillOpacity: 0.85,
      weight: 2,
    });
  }

  private setSelectedPoint(lat: number, lng: number): void {
    this.selectedLat = lat;
    this.selectedLng = lng;
    this.loadAddressFromCoords(this.selectedLat, this.selectedLng);

    if (this.selectedPointMarker) {
      this.selectedPointMarker.setLatLng([lat, lng]);
    } else {
      const pinIcon = L.icon({
        iconUrl: 'assets/pin.svg',
        iconSize: [40, 40],
        iconAnchor: [20, 37],
        popupAnchor: [0, -40],
      });

      this.selectedPointMarker = L.marker([lat, lng], {
        draggable: true,
        icon: pinIcon,
      }).addTo(this.map);

      this.selectedPointMarker.on('dragend', () => {
        const marker = this.selectedPointMarker;
        if (marker) {
          const position = marker.getLatLng();
          this.selectedLat = position.lat;
          this.selectedLng = position.lng;
          this.loadAddressFromCoords(position.lat, position.lng);
        }
      });
    }

    const button = document.createElement('button');

    button.type = 'button';
    button.className = 'create-complaint-button';
    button.textContent = 'Сообщить о проблеме';

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      event.preventDefault();
      this.createComplaint();
    });

    if (!this.isComplaintFormOpen()) {
      this.selectedPointMarker.bindPopup(button).openPopup();
    }
  }

  private addDistricts(): void {
    fetch('assets/districts_perm.geojson')
      .then((res) => res.json())
      .then((data) => {
        this.districtsLayer = L.geoJSON(data, {
          style: {
            color: '#2563eb',
            weight: 2,
            fillColor: '#3b82f6',
            fillOpacity: 0.15,
          },
        }).addTo(this.map);

        const cityBounds = this.districtsLayer.getBounds();

        if (cityBounds.isValid()) {
          this.map.setMaxBounds(cityBounds);
          this.map.fitBounds(cityBounds);
        }
      });
  }

  private loadReports(): void {
    this.apiService.getNearbyReports().subscribe((reports) => {
      if (!reports) {
        return;
      }

      this.complaints = reports.map((report: Report) => {
        const [lng, lat] = report.location.coordinates;

        return {
          id: report.id,
          title: report.title,
          type: report.issue_type ?? 'other',
          district: '',
          lat,
          lng,
          status: (report.status ?? 'pending') as Complaint['status'],
        };
      });

      this.applyFilters();
    });
  }

  private loadAddressFromCoords(lat: number, lng: number): void {
    this.selectedAddress.set('Определяем адрес...');

    this.apiService.loadAddress(lat, lng).subscribe({
      next: (data) => {
        this.selectedAddress.set(data.display_name || 'Адрес не найден');
      },
      error: () => {
        this.selectedAddress.set('Адрес не найден');
      },
    });
  }

  private initUserLocationMarker(): void {
    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        this.setSelectedPoint(lat, lng);

        this.map.setView([lat, lng], 15);
      },
      (error) => {
        console.warn(
          'Пользователь не дал доступ к геолокации или произошла ошибка:',
          error,
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  }
}
