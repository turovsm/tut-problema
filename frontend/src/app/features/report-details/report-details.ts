import { CommonModule, DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { environment } from '../../../environments/environment';
import {
  MapWidgetApiService,
  ReportDetails,
} from '../map-widget/map-widget-api.service';

import { IssueType, ISSUE_TYPE_LABELS } from '../../core/models/issue-type';
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
    MatProgressSpinnerModule,
    MatFormFieldModule,
    MatInputModule,
  ],
})
export class ReportDetailsComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly apiService = inject(MapWidgetApiService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly http = inject(HttpClient);

  report = signal<ReportDetails | null>(null);
  isLoading = signal(false);
  isVoting = signal(false);
  isDeletingPhoto = signal(false);
  isResolvingReport = signal(false);
  errorMessage = signal('');
  moderationErrorMessage = signal('');
  moderationSuccessMessage = signal('');
  resolveComment = signal('');
  resolveFiles = signal<File[]>([]);

  geoErrorMessage = signal('');

  currentUser = this.authService.currentUser();
  currentUserId = this.currentUser?.id;

  isModerator = computed(() => {
    const role = this.currentUser?.role;
    return role === 'moderator';
  });

  isOwnReport = computed(() => {
    const report = this.report();

    if (!report || !this.currentUserId) {
      return false;
    }

    return report.created_by.id === this.currentUserId;
  });

  isAssignedToMe = computed(() => {
    const report = this.report();
    if (!report || !this.currentUserId) {
      return false;
    }
    return report.assigned_to?.id === this.currentUserId;
  });

  canVote = computed(() => {
    return Boolean(this.report()) && !this.isOwnReport() && !this.isVoting();
  });

  ngOnInit(): void {
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
      next: (report) => {
        this.report.set(report);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Ошибка загрузки жалобы:', error);
        this.errorMessage.set(
          error.error?.message || 'Не удалось загрузить жалобу',
        );
        this.isLoading.set(false);
      },
    });
  }

  vote(voteType: 'confirm' | 'dismiss'): void {
    const report = this.report();

    if (!report) {
      return;
    }

    if (this.isOwnReport()) {
      alert('Нельзя голосовать за свою жалобу');
      return;
    }

    this.isVoting.set(true);

    const cappedAccuracy = 0;

    this.apiService
      .voteForReport(report.id, {
        vote_type: voteType,
        user_location_lng: report.location.coordinates[0],
        user_location_lat: report.location.coordinates[1],
        accuracy: cappedAccuracy,
      })
      .subscribe({
        next: () => {
          this.isVoting.set(false);
          this.loadReport();
        },
        error: (error) => {
          console.error('Ошибка голосования:', error);
          this.isVoting.set(false);

        if (error.status === 401) {
          alert('Необходимо авторизоваться');
          return;
        }

          if (error.status === 403) {
            if (error.error?.error === 'Email not verified.') {
              alert('Подтвердите почту для голосования за проблему');
            } else if (error.error?.error === 'You cannot vote on your own report'){
              alert('Нельзя голосовать за свою заявку');
            } else {
              alert(
                'Вы не можете голосовать: возможно, жалоба вне разрешённого радиуса',
              );
            }

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
      error: (error) => {
        console.error('Ошибка снятия голоса:', error);
        this.isVoting.set(false);
        alert(error.error?.message || 'Не удалось снять голос');
      },
    });
  }

  editReport(): void {
    const report = this.report();

    if (!report) {
      return;
    }

    this.router.navigate(['/reports', report.id, 'edit']);
  }

  onResolveFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.resolveFiles.set(Array.from(input.files ?? []));
  }

  removeResolveFile(fileToRemove: File): void {
    this.resolveFiles.update((files) =>
      files.filter((file) => file !== fileToRemove),
    );
  }

  deletePhoto(photoId: string): void {
    if (!this.isModerator()) {
      return;
    }

    const shouldDelete = confirm('Удалить это фото как неподходящее?');

    if (!shouldDelete) {
      return;
    }

    this.isDeletingPhoto.set(true);
    this.moderationErrorMessage.set('');
    this.moderationSuccessMessage.set('');

    this.http
      .delete(`${environment.apiUrl}/api/uploads/photos/${photoId}`, {
        withCredentials: true,
      })
      .subscribe({
        next: () => {
          this.isDeletingPhoto.set(false);
          this.moderationSuccessMessage.set('Фото удалено');
          this.loadReport();
        },
        error: (error) => {
          console.error('Ошибка удаления фото:', error);
          this.isDeletingPhoto.set(false);
          this.moderationErrorMessage.set(
            error.error?.message || 'Не удалось удалить фото',
          );
        },
      });
  }

  isUploadingResPhoto = signal(false);

  deleteResolutionPhoto(photoId: string): void {
    if (!this.isModerator()) return;
    if (!confirm('Удалить это фото из отчёта?')) return;

    this.http
      .delete(
        `${environment.apiUrl}/api/uploads/resolutions/photos/${photoId}`,
        {
          withCredentials: true,
        },
      )
      .subscribe({
        next: () => {
          this.loadReport();
        },
        error: (error) => {
          console.error('Ошибка удаления фото отчёта:', error);
          alert(
            error.error?.detail ||
              error.error?.message ||
              'Не удалось удалить фото',
          );
        },
      });
  }

  uploadResolutionPhoto(event: Event, resolutionId: string): void {
    if (!this.isModerator()) return;

    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    this.isUploadingResPhoto.set(true);

    this.http
      .post(
        `${environment.apiUrl}/api/uploads/resolutions/${resolutionId}/photos`,
        formData,
        {
          withCredentials: true,
        },
      )
      .subscribe({
        next: () => {
          this.isUploadingResPhoto.set(false);
          input.value = '';
          this.loadReport();
        },
        error: (error) => {
          console.error('Ошибка загрузки фото отчёта:', error);
          this.isUploadingResPhoto.set(false);
          input.value = '';
          alert(
            error.error?.detail ||
              error.error?.message ||
              'Не удалось загрузить фото',
          );
        },
      });
  }

  resolveReport(): void {
    const report = this.report();

    if (!report || !this.isAssignedToMe()) {
      return;
    }

    const comment = this.resolveComment().trim();

    if (!comment) {
      this.moderationErrorMessage.set('Добавьте комментарий к выполнению');
      return;
    }

    const formData = new FormData();
    formData.append('comment', comment);

    const files = this.resolveFiles();

    if (files.length > 0) {
      files.forEach((file) => {
        formData.append('files', file, file.name);
      });
    }

    this.isResolvingReport.set(true);
    this.moderationErrorMessage.set('');
    this.moderationSuccessMessage.set('');

    this.http
      .post(
        `${environment.apiUrl}/api/reports/${report.id}/resolve`,
        formData,
        {
          withCredentials: true,
        },
      )
      .subscribe({
        next: () => {
          this.isResolvingReport.set(false);
          this.resolveComment.set('');
          this.resolveFiles.set([]);
          this.moderationSuccessMessage.set('Отчет отправлен, жалоба закрыта');
          this.loadReport();
        },
        error: (error) => {
          console.error('Ошибка отправки отчета:', error);
          this.isResolvingReport.set(false);
          this.moderationErrorMessage.set(
            error.error?.message || 'Не удалось отправить отчет',
          );
        },
      });
  }

  getIssueLabel(type: IssueType | string): string {
    return ISSUE_TYPE_LABELS[type as IssueType] ?? type;
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      pending: 'На рассмотрении',
      confirmed: 'Подтверждена',
      dismissed: 'Отклонена',
      resolved: 'Решена',
    };

    return labels[status] ?? status;
  }

  getVoteLabel(vote: 'confirm' | 'dismiss' | null): string {
    if (vote === 'confirm') {
      return 'подтверждение';
    }

    if (vote === 'dismiss') {
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
}
