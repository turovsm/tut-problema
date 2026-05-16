import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AuthService } from '../../core/auth/auth.service';
import { ProfileApiService } from './profile-api.service';
import { ReportCardComponent } from '../../shared/report-card/report-card.component';
import { MyReport } from '../../core/models/report.models';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgClass,
    MatCardModule,
    MatButtonModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    ReportCardComponent
  ],
  templateUrl: './profile.html',
  styleUrl: './profile.less'
})
export class ProfilePageComponent implements OnInit {
  private readonly profileApi = inject(ProfileApiService);
  private readonly router = inject(Router);

  private readonly authService = inject(AuthService);
  readonly user = this.authService.currentUser;

  readonly isVerified = computed(() => {
    return this.user()?.is_verified ?? false;
  });

  reports: MyReport[] = [];

  isLoadingReports = signal(false);
  errorMessage = '';

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
}