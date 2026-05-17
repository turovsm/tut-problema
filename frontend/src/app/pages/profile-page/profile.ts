import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import {
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import {
  MatDialog,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AuthService } from '../../core/auth/auth.service';
import { ProfileApiService } from './profile-api.service';
import { ReportCardComponent } from '../../shared/report-card/report-card.component';
import { MyReport } from '../../core/models/report.models';

function passwordMatchValidator(
  control: AbstractControl,
): ValidationErrors | null {
  const newPassword = control.get('newPassword')?.value;
  const confirmPassword = control.get('confirmPassword')?.value;

  if (!newPassword || !confirmPassword) {
    return null;
  }

  return newPassword === confirmPassword ? null : { passwordMismatch: true };
}

@Component({
  selector: 'app-change-password-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <h2 mat-dialog-title>Смена пароля</h2>

    <form [formGroup]="passwordForm" (ngSubmit)="submitPasswordChange()">
      <mat-dialog-content class="password-dialog-content">
        <mat-form-field appearance="outline">
          <mat-label>Текущий пароль</mat-label>
          <input
            matInput
            type="password"
            formControlName="currentPassword"
            autocomplete="current-password"
          />
          @if (passwordForm.controls.currentPassword.hasError('required')) {
            <mat-error>Введите текущий пароль</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Новый пароль</mat-label>
          <input
            matInput
            type="password"
            formControlName="newPassword"
            autocomplete="new-password"
          />
          @if (passwordForm.controls.newPassword.hasError('required')) {
            <mat-error>Введите новый пароль</mat-error>
          }
          @if (passwordForm.controls.newPassword.hasError('minlength')) {
            <mat-error>Минимум 8 символов</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Повторите новый пароль</mat-label>
          <input
            matInput
            type="password"
            formControlName="confirmPassword"
            autocomplete="new-password"
          />
          @if (passwordForm.controls.confirmPassword.hasError('required')) {
            <mat-error>Повторите новый пароль</mat-error>
          }
          @if (
            passwordForm.hasError('passwordMismatch') &&
            passwordForm.controls.confirmPassword.touched
          ) {
            <mat-error>Пароли не совпадают</mat-error>
          }
        </mat-form-field>

        @if (passwordErrorMessage) {
          <div class="password-error">
            {{ passwordErrorMessage }}
          </div>
        }
      </mat-dialog-content>

      <mat-dialog-actions align="end">
        <button
          mat-button
          type="button"
          [disabled]="isChangingPassword()"
          (click)="dialogRef.close(false)"
        >
          Отмена
        </button>

        <button
          mat-raised-button
          color="primary"
          type="submit"
          [disabled]="passwordForm.invalid || isChangingPassword()"
        >
          @if (isChangingPassword()) {
            <mat-spinner diameter="20"></mat-spinner>
          } @else {
            Сохранить
          }
        </button>
      </mat-dialog-actions>
    </form>
  `,
  styles: [
    `
      .password-dialog-content {
        display: flex;
        flex-direction: column;
        gap: 12px;
        min-width: 360px;
        padding-top: 8px;
      }

      .password-error {
        padding: 10px 12px;
        border-radius: 8px;
        background: #fdecea;
        color: #b71c1c;
      }

      mat-dialog-actions button[type='submit'] {
        min-width: 120px;
      }

      mat-spinner {
        display: inline-block;
      }

      @media (max-width: 480px) {
        .password-dialog-content {
          min-width: 0;
        }
      }
    `,
  ],
})
export class ChangePasswordDialogComponent {
  private readonly authService = inject(AuthService);
  private readonly fb = inject(NonNullableFormBuilder);

  readonly dialogRef = inject(
    MatDialogRef<ChangePasswordDialogComponent, boolean>,
  );
  readonly isChangingPassword = signal(false);

  passwordErrorMessage = '';

  readonly passwordForm = this.fb.group(
    {
      currentPassword: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
    },
    { validators: passwordMatchValidator },
  );

  submitPasswordChange(): void {
    this.passwordErrorMessage = '';

    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      return;
    }

    const { currentPassword, newPassword } = this.passwordForm.getRawValue();

    this.isChangingPassword.set(true);

    this.authService.changePassword(currentPassword, newPassword).subscribe({
      next: () => {
        this.isChangingPassword.set(false);
        this.dialogRef.close(true);
      },
      error: (error) => {
        console.error('Ошибка смены пароля:', error);
        this.passwordErrorMessage =
          error?.error?.message || 'Не удалось изменить пароль';
        this.isChangingPassword.set(false);
      },
    });
  }
}

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
    MatDialogModule,
    MatSnackBarModule,
    ReportCardComponent,
  ],
  templateUrl: './profile.html',
  styleUrl: './profile.less',
})
export class ProfilePageComponent implements OnInit {
  private readonly profileApi = inject(ProfileApiService);
  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

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
      next: (reports) => {
        this.reports = reports;
        this.isLoadingReports.set(false);
      },
      error: (error) => {
        console.error('Ошибка загрузки жалоб пользователя:', error);
        this.errorMessage = 'Не удалось загрузить ваши жалобы';
        this.isLoadingReports.set(false);
      },
    });
  }

  openChangePasswordDialog(): void {
    const dialogRef = this.dialog.open(ChangePasswordDialogComponent, {
      width: '440px',
      maxWidth: 'calc(100vw - 32px)',
      disableClose: true,
    });

    dialogRef.afterClosed().subscribe((isPasswordChanged) => {
      if (!isPasswordChanged) {
        return;
      }

      this.snackBar.open('Пароль успешно изменён', 'Закрыть', {
        duration: 4000,
      });
    });
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.router.navigate(['/auth/login']);
      },
      error: (error) => {
        console.error('Ошибка выхода:', error);
        this.router.navigate(['/auth/login']);
      },
    });
  }
}
