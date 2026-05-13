import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { MyReport } from '../../core/models/report.models';
import { ApiResponseSuccess, PaginatedResponse } from '../../core/models/response.model';

@Injectable({
  providedIn: 'root'
})
export class ReportsApiService {
  private readonly apiUrl = environment.apiUrl;
  private readonly http = inject(HttpClient);

  getReports(page = 1, limit = 20): Observable<PaginatedResponse<MyReport>> {
    const params = new HttpParams()
      .set('page', page)
      .set('limit', limit);

    return this.http
      .get<ApiResponseSuccess<PaginatedResponse<MyReport>>>(`${this.apiUrl}/api/reports`, {
        params,
        withCredentials: true
      })
      .pipe(map(response => response.data));
  }
}
