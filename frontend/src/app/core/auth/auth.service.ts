import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponseSuccess } from '../models/response.model';

export interface LoginRequest {
  email: string;
  password: string;
  remember_me: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

export interface VerifyEmailRequest {
  code: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface User {
  email: string;
  username: string;
  id: string;
  role: 'user' | 'gov_org' | 'moderator';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly currentUserSignal = signal<User | null>(null);

  readonly currentUser = this.currentUserSignal.asReadonly();
  readonly isAuthenticated = computed(() => !!this.currentUserSignal());

  initializeAuth(): Promise<void> {
    return new Promise(resolve => {
      this.me().subscribe({
        next: user => {
          this.currentUserSignal.set(user.data);
          resolve();
        },
        error: () => {
          this.currentUserSignal.set(null);
          resolve();
        }
      });
    });
  }

  login(data: LoginRequest): Observable<ApiResponseSuccess<User>> {
    return this.http.post<ApiResponseSuccess<User>>(`${environment.apiUrl}/api/auth/login`, data, {
      withCredentials: true
    }).pipe(
      tap(response => this.currentUserSignal.set(response.data))
    );
  }

  register(data: RegisterRequest): Observable<ApiResponseSuccess<User>> {
    return this.http.post<ApiResponseSuccess<User>>(`${environment.apiUrl}/api/auth/register`, data, {
      withCredentials: true
    }).pipe(
      tap(response => this.currentUserSignal.set(response.data))
    );
  }

  me(): Observable<ApiResponseSuccess<User>> {
    return this.http.get<ApiResponseSuccess<User>>(`${environment.apiUrl}/api/users/me`, {
      withCredentials: true
    }).pipe(
      tap(response => this.currentUserSignal.set(response.data))
    );
  }

  logout(): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/api/auth/logout`, {}, {
      withCredentials: true
    }).pipe(
      tap(() => this.currentUserSignal.set(null))
    );
  }

  verifyEmail(token: string): Observable<ApiResponseSuccess<null>> {
    return this.http.post<ApiResponseSuccess<null>>(`${environment.apiUrl}/api/auth/verify-email`, {
      token
    }, {
      withCredentials: true
    });
  }

  sendVerification(email: string): Observable<ApiResponseSuccess<null>> {
    return this.http.post<ApiResponseSuccess<null>>(`${environment.apiUrl}/api/auth/resend-verification`, {
      email
    }, {
      withCredentials: true
    });
  }

  changePassword(currentPassword: string, newPassword: string): Observable<ApiResponseSuccess<null>> {
    return this.http.post<ApiResponseSuccess<null>>(`${environment.apiUrl}/api/auth/change-password`, {
      current_password: currentPassword,
      new_password: newPassword
    }, {
      withCredentials: true
    });
  }

  forgotPassword(email: string): Observable<ApiResponseSuccess<null>> {
    return this.http.post<ApiResponseSuccess<null>>(`${environment.apiUrl}/api/auth/forgot-password`, {
      email
    });
  }

  resetPassword(token: string, newPassword: string): Observable<ApiResponseSuccess<null>> {
    return this.http.post<ApiResponseSuccess<null>>(`${environment.apiUrl}/api/auth/reset-password`, {
      token,
      new_password: newPassword
    });
  }
}
