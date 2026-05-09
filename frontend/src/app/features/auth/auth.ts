import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { LoginFormComponent } from './login-form/login-form.component';
import { RegisterFormComponent } from './register-form/register-form.component';

export type AuthDialogMode = 'login' | 'register';

export interface AuthDialogData {
  mode: AuthDialogMode;
}

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    LoginFormComponent,
    RegisterFormComponent
  ],
  templateUrl: './auth.html',
  styleUrls: ['./auth.less']
})
export class AuthComponent {
  private readonly data: AuthDialogData = inject(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<AuthComponent>);

  mode = signal<AuthDialogMode>(this.data.mode);

  switchToLogin(): void {
    this.mode.set('login');
  }

  switchToRegister(): void {
    this.mode.set('register');
  }

  close(): void {
    this.dialogRef.close();
  }

  closeAfterSuccess(): void {
    this.dialogRef.close(true);
  }
}