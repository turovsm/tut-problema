import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';

import { AuthService } from '../../../core/auth/auth.service';
import { take } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-register-form',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
  ],
  templateUrl: './register-form.component.html',
  styleUrls: ['./register-form.component.less']
})
export class RegisterFormComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);

  readonly isLoading = signal(false);
  readonly error = signal('');

  @Output() registered = new EventEmitter<string>();
  @Output() goToLogin = new EventEmitter<void>();

  hidePassword = true;

  form = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [
        Validators.required,
        Validators.minLength(8),
        Validators.pattern(/[0-9]/),
        Validators.pattern(/[a-z]/),
        Validators.pattern(/[A-Z]/),
        Validators.pattern(/[@$!%*?&]/)
      ]
    ]
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.error.set('');

    const email = this.form.value.email ?? '';

    this.authService.register({
      username: this.form.value.name ?? '',
      email,
      password: this.form.value.password ?? ''
    }).pipe(take(1)).subscribe({
      next: () => {
        this.registered.emit(email);
        this.isLoading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.error.set(this.getErrorText(err));
        this.isLoading.set(false);
      }
    });
  }

  getErrorText(err: HttpErrorResponse): string {
    if (err.error?.detail === 'Email already registered') {
      return 'На эту почту уже зарегистрирован аккаунт';
    } else if (err.error?.detail === 'Username already taken') {
      return 'Этот никнейм занят';
    }
    return 'Произошла ошибка регистрации';
  }
}
