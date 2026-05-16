import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { take } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';

import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
  ],
  templateUrl: './verify-email.component.html',
  styleUrls: ['./verify-email.component.less']
})
export class VerifyEmailComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);

  @Input({ required: true }) email = '';

  @Output() success = new EventEmitter<void>();
  @Output() goToLogin = new EventEmitter<void>();

  readonly isLoading = signal(false);
  readonly isResending = signal(false);
  readonly error = signal('');
  readonly message = signal('');

  resendCode(): void {
    if (!this.email) {
      this.error.set('Email не найден. Вернитесь к регистрации и попробуйте ещё раз');
      return;
    }

    this.isResending.set(true);
    this.error.set('');
    this.message.set('');

    this.authService.sendVerification(this.email).pipe(take(1)).subscribe({
      next: () => {
        this.message.set('Код подтверждения отправлен повторно');
        this.isResending.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.error.set(this.getResendErrorText(err));
        this.isResending.set(false);
      }
    });
  }

  private getVerifyErrorText(err: HttpErrorResponse): string {
    if (err.error?.detail === 'Invalid verification token') {
      return 'Неверный код подтверждения';
    }

    if (err.error?.detail === 'Verification token expired') {
      return 'Код подтверждения истёк. Запросите новый код';
    }

    return 'Не удалось подтвердить email';
  }

  private getResendErrorText(err: HttpErrorResponse): string {
    if (err.error?.detail === 'User not found') {
      return 'Пользователь с таким email не найден';
    }

    return 'Не удалось отправить код повторно';
  }
}
