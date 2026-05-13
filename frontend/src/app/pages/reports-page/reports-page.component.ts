import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ReportsApiService } from './reports-page-api.service';
import { ReportCardComponent } from '../../shared/report-card/report-card.component';
import { MyReport } from '../../core/models/report.models';
import { PaginatedResponse } from '../../core/models/response.model';

@Component({
  selector: 'app-reports-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule,
    ReportCardComponent
  ],
  templateUrl: './reports-page.component.html',
  styleUrl: './reports-page.component.less'
})
export class ReportsPageComponent implements OnInit {
  private readonly reportsApiService = inject(ReportsApiService);
  readonly reports = signal<MyReport[]>([]);
  readonly isLoadingReports = signal(false);
  readonly isLoadingMoreReports = signal(false);
  readonly errorMessage = signal('');

  readonly page = signal(1);
  readonly limit = 20;
  readonly total = signal(0);
  readonly hasNext = signal(false);

  ngOnInit(): void {
    this.loadReports();
  }

  loadReports(page = 1): void {
    const isFirstPage = page === 1;

    if (isFirstPage) {
      this.isLoadingReports.set(true);
      this.errorMessage.set('');
    } else {
      this.isLoadingMoreReports.set(true);
    }

    this.reportsApiService.getReports(page, this.limit).subscribe({
      next: response => {
        this.applyReportsResponse(response, isFirstPage);
        this.isLoadingReports.set(false);
        this.isLoadingMoreReports.set(false);
      },
      error: error => {
        console.error('Ошибка загрузки жалоб:', error);
        this.errorMessage.set('Не удалось загрузить жалобы');
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
