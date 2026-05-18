import { Component, inject, signal } from '@angular/core';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { LoginFormComponent } from './login-form/login-form.component';
import { RegisterFormComponent } from './register-form/register-form.component';
import { VerifyEmailComponent } from './verify-email/verify-email.component';

export type AuthDialogMode = 'login' | 'register' | 'verify-email';

export interface AuthDialogData {
  mode: AuthDialogMode;
}

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    LoginFormComponent,
    RegisterFormComponent,
    VerifyEmailComponent,
  ],
  templateUrl: './auth.html',
  styleUrls: ['./auth.less'],
})
export class AuthComponent {
  private readonly data: AuthDialogData = inject(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<AuthComponent>);

  mode = signal<AuthDialogMode>(this.data.mode);
  verificationEmail = signal('');

  switchToLogin(): void {
    this.mode.set('login');
  }

  switchToRegister(): void {
    this.mode.set('register');
  }

  switchToVerifyEmail(email: string): void {
    this.verificationEmail.set(email);
    this.mode.set('verify-email');
  }

  close(): void {
    this.dialogRef.close();
  }

  closeAfterSuccess(): void {
    this.dialogRef.close(true);
  }
}
