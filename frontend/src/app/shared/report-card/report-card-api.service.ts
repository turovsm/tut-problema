import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ReportVoteStats } from '../../core/models/report.models';
import { ApiResponseSuccess } from '../../core/models/response.model';

@Injectable({
  providedIn: 'root'
})
export class ReportCardApiService {
  private readonly apiUrl = environment.apiUrl;
  private readonly http = inject(HttpClient);

  getReportVoteStats(reportId: string): Observable<ReportVoteStats> {
    return this.http
      .get<ApiResponseSuccess<ReportVoteStats>>(`${this.apiUrl}/api/votes/reports/${reportId}/stats`, { withCredentials: true })
      .pipe(map(response => response.data));
  }
}
