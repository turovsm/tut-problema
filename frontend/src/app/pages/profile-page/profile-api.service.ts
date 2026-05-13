import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse, MyReport, PaginatedResponse, UserProfile } from './profile.models';

@Injectable({
  providedIn: 'root'
})
export class ProfileApiService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  getCurrentUser(): Observable<UserProfile> {
    return this.http
      .get<ApiResponse<UserProfile>>(`${this.apiUrl}/api/users/me`, { withCredentials: true })
      .pipe(map(response => response.data));
  }

  getMyReports(): Observable<MyReport[]> {
    return this.http
      .get<ApiResponse<PaginatedResponse<MyReport>>>(`${this.apiUrl}/api/reports/user/me`, { withCredentials: true })
      .pipe(map(response => response.data.items));
  }
}
