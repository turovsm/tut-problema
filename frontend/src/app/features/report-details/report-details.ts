import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { environment } from '../../../environments/environment';
import {
  MapWidgetApiService,
  ReportDetails
} from '../map-widget/map-widget-api.service';

import {
  IssueType,
  ISSUE_TYPE_LABELS
} from '../../core/models/issue-type';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-report-detail',
  standalone: true,
  templateUrl: './report-details.html',
  styleUrls: ['./report-details.less'],
  imports: [
    CommonModule,
    RouterModule,
    DatePipe,
    MatCardModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ]
})
export class ReportDetailsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly apiService = inject(MapWidgetApiService);
  private readonly authService = inject(AuthService);

  report = signal<ReportDetails | null>(null);
  isLoading = signal(false);
  isVoting = signal(false);
  errorMessage = signal('');

  userLocation = signal<GeolocationCoordinates | null>(null);
  geoErrorMessage = signal('');

   currentUserId = this.authService.currentUser()?.id;

  isOwnReport = computed(() => {
    const report = this.report();

    if (!report || !this.currentUserId) {
      return false;
    }

    return report.created_by.id === this.currentUserId;
  });

  canVote = computed(() => {
    return Boolean(this.report()) && !this.isOwnReport() && !this.isVoting();
  });

  ngOnInit(): void {
    this.loadUserLocation();
    this.loadReport();
  }

  loadReport(): void {
    const reportId = this.route.snapshot.paramMap.get('report_id');

    if (!reportId) {
      this.errorMessage.set('ID жалобы не найден');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    this.apiService.getReportById(reportId).subscribe({
      next: report => {
        this.report.set(report);
        this.isLoading.set(false);
      },
      error: error => {
        console.error('Ошибка загрузки жалобы:', error);
        this.errorMessage.set(
          error.error?.message || 'Не удалось загрузить жалобу'
        );
        this.isLoading.set(false);
      }
    });
  }

  vote(voteType: 'confirm' | 'reject'): void {
    const report = this.report();
    const coords = this.userLocation();

    if (!report) {
      return;
    }

    if (this.isOwnReport()) {
      alert('Нельзя голосовать за свою жалобу');
      return;
    }

    if (!coords) {
      alert('Для голосования нужно разрешить доступ к геолокации');
      this.loadUserLocation();
      return;
    }

    this.isVoting.set(true);

    this.apiService.voteForReport(report.id, {
      vote_type: voteType,
      user_location_lng: coords.longitude,
      user_location_lat: coords.latitude,
      accuracy: coords.accuracy
    }).subscribe({
      next: () => {
        this.isVoting.set(false);
        this.loadReport();
      },
      error: error => {
        console.error('Ошибка голосования:', error);
        this.isVoting.set(false);

        if (error.status === 401) {
          alert('Необходимо авторизоваться');
          return;
        }

        if (error.status === 403) {
          alert('Вы не можете голосовать: возможно, жалоба вне разрешённого радиуса');
          return;
        }

        if (error.status === 409) {
          alert('Вы уже голосовали за эту жалобу');
          return;
        }

        alert(error.error?.message || 'Не удалось отправить голос');
      }
    });
  }

  removeVote(): void {
    const report = this.report();

    if (!report) {
      return;
    }

    this.isVoting.set(true);

    this.apiService.removeReportVote(report.id).subscribe({
      next: () => {
        this.isVoting.set(false);
        this.loadReport();
      },
      error: error => {
        console.error('Ошибка снятия голоса:', error);
        this.isVoting.set(false);
        alert(error.error?.message || 'Не удалось снять голос');
      }
    });
  }

  editReport(): void {
    // Пока без действий.
    // Потом сюда можно добавить router.navigate(['/reports', id, 'edit'])
    console.log('Редактирование жалобы пока не реализовано');
  }

  getIssueLabel(type: IssueType | string): string {
    return ISSUE_TYPE_LABELS[type as IssueType] ?? type;
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      pending: 'На рассмотрении',
      confirmed: 'Подтверждена',
      rejected: 'Отклонена',
      resolved: 'Решена',
      closed: 'Закрыта'
    };

    return labels[status] ?? status;
  }

  getVoteLabel(vote: 'confirm' | 'reject' | null): string {
    if (vote === 'confirm') {
      return 'подтверждение';
    }

    if (vote === 'reject') {
      return 'отклонение';
    }

    return 'нет';
  }

  getPhotoUrl(fileUrl: string): string {
    if (fileUrl.startsWith('http')) {
      return fileUrl;
    }

    return `${environment.apiUrl}${fileUrl}`;
  }

  private loadUserLocation(): void {
    this.geoErrorMessage.set('');

    if (!navigator.geolocation) {
      this.geoErrorMessage.set('Геолокация не поддерживается браузером');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        this.userLocation.set(position.coords);
        this.geoErrorMessage.set('');
      },
      error => {
        console.warn('Геолокация недоступна:', error);
        this.geoErrorMessage.set(
          'Геолокация недоступна. Без неё нельзя голосовать.'
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  }
}