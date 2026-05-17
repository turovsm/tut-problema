import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { take } from 'rxjs';

import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-verify-email',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './verify-email.html',
  styleUrl: './verify-email.less',
})
export class VerifyEmailPage implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);

  readonly status = signal<'loading' | 'success' | 'error'>('loading');
  readonly errorText = signal('');
  readonly resendStatus = signal<'idle' | 'loading' | 'success' | 'error'>(
    'idle',
  );

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');

    if (!token) {
      this.status.set('error');
      this.errorText.set('Не найден токен верификации');
      return;
    }

    this.status.set('loading');

    this.authService
      .verifyEmail(token)
      .pipe(take(1))
      .subscribe({
        next: () => {
          this.status.set('success');
        },
        error: (err: HttpErrorResponse) => {
          this.status.set('error');

          if (err.status === 400) {
            this.errorText.set('Токен верификации устарел');
          } else {
            this.errorText.set('Произошла ошибка верификации');
          }
        },
      });
  }

  submit(): void {
    if (this.form.invalid || this.resendStatus() === 'loading') {
      this.form.markAllAsTouched();
      return;
    }

    this.resendStatus.set('loading');

    this.authService
      .sendVerification(this.form.controls.email.value)
      .pipe(take(1))
      .subscribe({
        next: () => {
          this.resendStatus.set('success');
        },
        error: () => {
          this.resendStatus.set('error');
        },
      });
  }
}
