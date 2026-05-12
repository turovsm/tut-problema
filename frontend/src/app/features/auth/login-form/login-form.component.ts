import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { AuthService } from '../../../core/auth/auth.service';
import { BehaviorSubject, catchError, EMPTY, take, tap, throwError } from 'rxjs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-login-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatCheckboxModule,
    MatProgressSpinnerModule,
    MatSnackBarModule
  ],
  templateUrl: './login-form.component.html',
  styleUrls: ['./login-form.component.less']
})
export class LoginFormComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly snackBar = inject(MatSnackBar);

  readonly isLoading = new BehaviorSubject(false);

  @Output() success = new EventEmitter<void>();
  @Output() goToRegister = new EventEmitter<void>();

  error = '';
  hidePassword = true;

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
    remember_me: [false, Validators.required]
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.next(true);
    this.error = '';

    this.authService.login({
      email: this.form.value.email ?? '',
      password: this.form.value.password ?? '',
      remember_me: this.form.value.remember_me ?? false
    }).pipe(take(1),catchError(() => {
        this.isLoading.next(false);
        return throwError(() => new Error('Something went wrong.'));
      })).subscribe({
      next: () => {
        this.snackBar.open('Вы успешно вошли', 'Закрыть', {
          duration: 3000,
          horizontalPosition: 'end',
          verticalPosition: 'top',
          panelClass: ['success-snackbar']
        });
        this.success.emit();
      },
      error: () => {this.error = 'Не удалось войти. Проверьте email и пароль.';},
      complete: () => {this.isLoading.next(false);}
    });
  }
}