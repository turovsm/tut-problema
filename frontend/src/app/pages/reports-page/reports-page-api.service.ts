import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { MyReport } from '../../core/models/report.models';
import { ApiResponseSuccess, PaginatedResponse } from '../../core/models/response.model';

export interface ReportsFilters {
  status?: string;
  district?: string;
  issue_type?: string;
  assigned_to_me?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ReportsApiService {
  private readonly apiUrl = environment.apiUrl;
  private readonly http = inject(HttpClient);

  getReports(
    page = 1,
    limit = 20,
    filters: ReportsFilters = {}
  ): Observable<PaginatedResponse<MyReport>> {
    let params = new HttpParams()
      .set('page', page)
      .set('limit', limit);

    if (filters.status) {
      params = params.set('status_filter', filters.status);
    }

    if (filters.district) {
      params = params.set('district', filters.district);
    }

    if (filters.issue_type) {
      params = params.set('issue_type', filters.issue_type);
    }

    if (filters.assigned_to_me) {
      params = params.set('assigned_to_me', 'true');
    }

    return this.http
      .get<ApiResponseSuccess<PaginatedResponse<MyReport>>>(`${this.apiUrl}/api/reports`, {
        params,
        withCredentials: true
      })
      .pipe(map(response => response.data));
  }
}
