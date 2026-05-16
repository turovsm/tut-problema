import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { MyReport, ReportVoteStats, UserProfile } from '../../core/models/report.models';
import { ApiResponseSuccess, PaginatedResponse } from '../../core/models/response.model';

@Injectable({
  providedIn: 'root'
})
export class ProfileApiService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl = environment.apiUrl;

  getCurrentUser(): Observable<UserProfile> {
    return this.http
      .get<ApiResponseSuccess<UserProfile>>(`${this.apiUrl}/api/users/me`, { withCredentials: true })
      .pipe(map(response => response.data));
  }

  getMyReports(): Observable<MyReport[]> {
    return this.http
      .get<ApiResponseSuccess<PaginatedResponse<MyReport>>>(`${this.apiUrl}/api/reports/user/me`, { withCredentials: true })
      .pipe(map(response => response.data.items));
  }

  getReportVoteStats(reportId: string): Observable<ReportVoteStats> {
    return this.http
      .get<ApiResponseSuccess<ReportVoteStats>>(`${this.apiUrl}/api/votes/reports/${reportId}/stats`, { withCredentials: true })
      .pipe(map(response => response.data));
  }
}
