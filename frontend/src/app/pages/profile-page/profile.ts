import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule, DatePipe, NgClass } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AuthService } from '../../core/auth/auth.service';
import { ProfileApiService } from './profile-api.service';
import { MyReport } from './profile.models';
import { ISSUE_TYPE_LABELS } from '../../core/models/issue-type';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    DatePipe,
    NgClass,
    MatCardModule,
    MatButtonModule,
    MatChipsModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './profile.html',
  styleUrl: './profile.less'
})
export class ProfilePageComponent implements OnInit {
  private readonly authService = inject(AuthService);
  readonly user = this.authService.currentUser;

  readonly isVerified = computed(() => {
    return this.user()?.is_verified ?? false;
  });

  reports: MyReport[] = [];

  isLoadingReports = signal(false);
  errorMessage = '';

  readonly issueTypeLabels = ISSUE_TYPE_LABELS;

  constructor(
    private readonly profileApi: ProfileApiService,
    private readonly router: Router
  ) {}

  ngOnInit(): void {
    if (!this.user()) {
      this.errorMessage = 'Пользователь не авторизован';
      return;
    }

    this.loadMyReports();
  }

  loadMyReports(): void {
    this.isLoadingReports.set(true);
    this.errorMessage = '';

    this.profileApi.getMyReports().subscribe({
      next: reports => {
        this.reports = reports;
        this.isLoadingReports.set(false);
      },
      error: error => {
        console.error('Ошибка загрузки жалоб пользователя:', error);
        this.errorMessage = 'Не удалось загрузить ваши жалобы';
        this.isLoadingReports.set(false);
      }
    });
  }

  getIssueTypeLabel(report: MyReport): string {
    return this.issueTypeLabels[report.issue_type] ?? report.issue_type;
  }

  getStatusLabel(status: MyReport['status']): string {
    const labels: Record<MyReport['status'], string> = {
      pending: 'Ожидает',
      confirmed: 'Подтверждена',
      dismissed: 'Отклонена',
      resolved: 'Решена'
    };

    return labels[status] ?? status;
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.router.navigate(['/auth/login']);
      },
      error: error => {
        console.error('Ошибка выхода:', error);
        this.router.navigate(['/auth/login']);
      }
    });
  }

  getReportPhotoUrl(report: MyReport): string {
    const fileUrl = report.photos?.[0]?.file_url;

    if (!fileUrl) {
      return '';
    }

    if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
      return fileUrl;
    }

    return `${environment.apiUrl}${fileUrl}`;
  }
}