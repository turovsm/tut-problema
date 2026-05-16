import { Component, inject, Input, OnInit, signal } from '@angular/core';
import { CommonModule, DatePipe, NgClass } from '@angular/common';
import { RouterLink } from '@angular/router';

import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { environment } from '../../../environments/environment';
import { ISSUE_TYPE_LABELS } from '../../core/models/issue-type';
import { ReportCardApiService } from './report-card-api.service';
import { MyReport, ReportVoteStats } from '../../core/models/report.models';



@Component({
  selector: 'app-report-card',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    DatePipe,
    NgClass,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './report-card.component.html',
  styleUrl: './report-card.component.less'
})
export class ReportCardComponent implements OnInit {
  private readonly reportCardApiService = inject(ReportCardApiService);
  @Input({ required: true }) report!: MyReport;

  readonly voteStats = signal<ReportVoteStats | null>(null);
  readonly isLoadingVoteStats = signal(false);
  readonly voteStatsError = signal(false);

  readonly issueTypeLabels = ISSUE_TYPE_LABELS;

  ngOnInit(): void {
    this.loadVoteStats();
  }

  loadVoteStats(): void {
    if (!this.report?.id) {
      return;
    }

    this.isLoadingVoteStats.set(true);
    this.voteStatsError.set(false);

    this.reportCardApiService.getReportVoteStats(this.report.id).subscribe({
      next: stats => {
        this.voteStats.set(stats);
        this.isLoadingVoteStats.set(false);
      },
      error: error => {
        console.error('Ошибка загрузки голосов жалобы:', error);
        this.voteStatsError.set(true);
        this.isLoadingVoteStats.set(false);
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
}
