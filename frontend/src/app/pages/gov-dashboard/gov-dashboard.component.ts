import { Component, inject, OnInit, signal } from '@angular/core';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';

import { ReportsApiService, ReportsFilters } from '../reports-page/reports-page-api.service';
import { ReportCardComponent } from '../../shared/report-card/report-card.component';
import { ISSUE_TYPE_LABELS } from '../../core/models/issue-type';
import { MyReport, REPORT_STATUS_OPTIONS } from '../../core/models/report.models';
import { PaginatedResponse } from '../../core/models/response.model';

@Component({
  selector: 'app-gov-dashboard',
  standalone: true,
  imports: [
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    ReportCardComponent
  ],
  templateUrl: './gov-dashboard.component.html',
  styleUrl: './gov-dashboard.component.less'
})
export class GovDashboardComponent implements OnInit {
  private readonly reportsApiService = inject(ReportsApiService);

  readonly reports = signal<MyReport[]>([]);
  readonly isLoadingReports = signal(false);
  readonly isLoadingMoreReports = signal(false);
  readonly errorMessage = signal('');

  readonly selectedStatus = signal('');
  readonly selectedIssueType = signal('');

  readonly page = signal(1);
  readonly limit = 20;
  readonly total = signal(0);
  readonly hasNext = signal(false);

  readonly statusOptions = REPORT_STATUS_OPTIONS;

  readonly issueTypeOptions = Object.entries(ISSUE_TYPE_LABELS).map(([value, label]) => ({
    value,
    label
  }));

  ngOnInit(): void {
    this.loadReports();
  }

  loadReports(page = 1): void {
    const isFirstPage = page === 1;

    if (isFirstPage) {
      this.isLoadingReports.set(true);
      this.errorMessage.set('');
      this.reports.set([]);
    } else {
      this.isLoadingMoreReports.set(true);
    }

    this.reportsApiService.getReports(page, this.limit, this.getFilters()).subscribe({
      next: response => {
        this.applyReportsResponse(response, isFirstPage);
        this.isLoadingReports.set(false);
        this.isLoadingMoreReports.set(false);
      },
      error: error => {
        console.error('Ошибка загрузки задач УК:', error);
        this.errorMessage.set('Не удалось загрузить задачи');
        this.isLoadingReports.set(false);
        this.isLoadingMoreReports.set(false);
      }
    });
  }

  loadMoreReports(): void {
    if (this.isLoadingMoreReports() || !this.hasNext()) {
      return;
    }
    this.loadReports(this.page() + 1);
  }

  onStatusChange(status: string): void {
    this.selectedStatus.set(status);
    this.loadReports();
  }

  onIssueTypeChange(issueType: string): void {
    this.selectedIssueType.set(issueType);
    this.loadReports();
  }

  resetFilters(): void {
    this.selectedStatus.set('');
    this.selectedIssueType.set('');
    this.loadReports();
  }

  hasActiveFilters(): boolean {
    return Boolean(this.selectedStatus() || this.selectedIssueType());
  }

  private getFilters(): ReportsFilters {
    return {
      status: this.selectedStatus() || undefined,
      issue_type: this.selectedIssueType() || undefined,
      assigned_to_me: true
    };
  }

  private applyReportsResponse(response: PaginatedResponse<MyReport>, isFirstPage: boolean): void {
    this.reports.set(isFirstPage
      ? response.items
      : [...this.reports(), ...response.items]
    );
    this.page.set(response.page);
    this.total.set(response.total);
    this.hasNext.set(response.has_next);
  }
}