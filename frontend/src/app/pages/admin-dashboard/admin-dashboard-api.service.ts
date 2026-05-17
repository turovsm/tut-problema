import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { UserProfile } from '../../core/models/report.models';
import {
  ApiResponseSuccess,
  PaginatedResponse,
} from '../../core/models/response.model';

@Injectable({
  providedIn: 'root',
})
export class AdminApiService {
  private readonly apiUrl = environment.apiUrl;
  private readonly http = inject(HttpClient);

  getUsers(page = 1, limit = 20): Observable<PaginatedResponse<UserProfile>> {
    const params = new HttpParams().set('page', page).set('limit', limit);

    return this.http
      .get<
        ApiResponseSuccess<PaginatedResponse<UserProfile>>
      >(`${this.apiUrl}/api/users/admin/users`, { params, withCredentials: true })
      .pipe(map((response) => response.data));
  }

  toggleUserStatus(userId: string, isActive: boolean): Observable<UserProfile> {
    return this.http
      .patch<
        ApiResponseSuccess<UserProfile>
      >(`${this.apiUrl}/api/users/admin/users/${userId}/status`, { is_active: isActive }, { withCredentials: true })
      .pipe(map((response) => response.data));
  }
}
