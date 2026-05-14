import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import {
  MapWidgetApiService,
  ReportDetails,
  UpdateReportBody
} from '../../map-widget/map-widget-api.service';

import {
  IssueType,
  ISSUE_TYPE_LABELS
} from '../../../core/models/issue-type';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-report-edit',
  standalone: true,
  templateUrl: './report-edit.html',
  styleUrls: ['./report-edit.less'],
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    DatePipe,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule
  ]
})
export class ReportEditComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly apiService = inject(MapWidgetApiService);

  govOrgs = signal<any[]>([]);
  isLoadingGovOrgs = signal(false);
  report = signal<ReportDetails | null>(null);
  isLoading = signal(false);
  isSaving = signal(false);
  isDeleting = signal(false);
  errorMessage = signal('');

  private readonly authService = inject(AuthService);
  currentUserId = this.authService.currentUser()?.id ?? '';
  currentUserRole = this.authService.currentUser()?.role ?? 'user';
  
  statuses = [
    { value: 'pending', label: 'На рассмотрении' },
    { value: 'confirmed', label: 'Подтверждена' },
    { value: 'dismissed', label: 'Отклонена' },
    { value: 'resolved', label: 'Решена' }
  ];

  form = this.fb.group({
    title: ['', [Validators.required, Validators.maxLength(120)]],
    description: ['', [Validators.required, Validators.maxLength(2000)]],
    status: ['pending', [Validators.required]],
    assigned_to_id: ['']
  });

  isOwnReport = computed(() => {
    const report = this.report();

    if (!report || !this.currentUserId) {
      return false;
    }

    return report.created_by.id === this.currentUserId;
  });

  isModeratorOrJkh = computed(() => {
    return [
      'gov_org',
      'moderator',
    ].includes(this.currentUserRole);
  });

  canEditTitleAndDescription = computed(() => {
    return this.isOwnReport();
  });

  canEditStatus = computed(() => {
    return this.isModeratorOrJkh();
  });

  canEditAnything = computed(() => {
    return this.canEditTitleAndDescription() || this.canEditStatus();
  });

  ngOnInit(): void {
    this.loadReport();
    if (this.currentUserRole === 'moderator') {
      this.loadGovOrgs();
    }
  }

  loadGovOrgs(): void {
    this.isLoadingGovOrgs.set(true);
    this.apiService.getGovOrgs().subscribe({
      next: orgs => {
        this.govOrgs.set(orgs);
        this.isLoadingGovOrgs.set(false);
      },
      error: () => this.isLoadingGovOrgs.set(false)
    });
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

        this.form.patchValue({
          title: report.title,
          description: report.description,
          status: report.status,
          assigned_to_id: report.assigned_to?.id || ''
        });

        this.applyPermissionsToForm();

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

  save(): void {
    const report = this.report();

    if (!report) {
      return;
    }

    if (!this.canEditAnything()) {
      alert('У вас нет прав на редактирование этой жалобы');
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const formValue = this.form.getRawValue();

    const body: UpdateReportBody = {};

    if (this.canEditTitleAndDescription()) {
      body.title = formValue.title ?? '';
      body.description = formValue.description ?? '';
    }

    if (this.canEditStatus()) {
      body.status = formValue.status ?? report.status;
    }

    if (this.currentUserRole === 'moderator' && formValue.assigned_to_id) {
      body.assigned_to_id = formValue.assigned_to_id;
    }

    this.isSaving.set(true);

    this.apiService.updateReport(report.id, body).subscribe({
      next: updatedReport => {
        this.isSaving.set(false);
        this.router.navigate(['/reports', updatedReport.id]);
      },
      error: error => {
        console.error('Ошибка обновления жалобы:', error);
        this.isSaving.set(false);

        if (error.status === 401) {
          alert('Необходимо авторизоваться');
          return;
        }

        if (error.status === 403) {
          alert('У вас нет прав на редактирование этой жалобы');
          return;
        }

        alert(error.error?.message || 'Не удалось сохранить изменения');
      }
    });
  }

  deleteReport(): void {
    const report = this.report();

    if (!report) {
      return;
    }

    const confirmed = confirm(
      'Удалить жалобу? Это действие нельзя отменить.'
    );

    if (!confirmed) {
      return;
    }

    this.isDeleting.set(true);

    this.apiService.deleteReport(report.id).subscribe({
      next: () => {
        this.isDeleting.set(false);
        this.router.navigate(['/']);
      },
      error: error => {
        console.error('Ошибка удаления жалобы:', error);
        this.isDeleting.set(false);

        if (error.status === 401) {
          alert('Необходимо авторизоваться');
          return;
        }

        if (error.status === 403) {
          alert('У вас нет прав на удаление этой жалобы');
          return;
        }

        alert(error.error?.message || 'Не удалось удалить жалобу');
      }
    });
  }

  cancel(): void {
    const report = this.report();

    if (report) {
      this.router.navigate(['/reports', report.id]);
      return;
    }

    this.router.navigate(['/']);
  }

  getIssueLabel(type: IssueType | string): string {
    return ISSUE_TYPE_LABELS[type as IssueType] ?? type;
  }

  getStatusLabel(status: string): string {
    return this.statuses.find(s => s.value === status)?.label ?? status;
  }

  private applyPermissionsToForm(): void {
    if (this.canEditTitleAndDescription()) {
      this.form.controls.title.enable();
      this.form.controls.description.enable();
    } else {
      this.form.controls.title.disable();
      this.form.controls.description.disable();
    }

    if (this.canEditStatus()) {
      this.form.controls.status.enable();
    } else {
      this.form.controls.status.disable();
    }
  }
}