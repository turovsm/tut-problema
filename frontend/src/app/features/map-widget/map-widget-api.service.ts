import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ApiResponseSuccess,
  PaginatedResponse,
} from '../../core/models/response.model';
import { IssueType } from '../../core/models/issue-type';
import { ReportStatus } from '../../core/models/report.models';

export interface ReportsResponse {
  status: 'success' | 'error';
  data: {
    items: Report[];
  };
  message: string;
}

export interface Report {
  id: string;
  title: string;
  description: string;
  issue_type: IssueType;
  location: {
    type: string;
    coordinates: [number, number]; // [lng, lat]
  };
  status: string;
  created_at: string;
  updated_at: string;
  photos: string[];
  user_vote: 'confirm' | 'dismiss' | null;
}

export interface ReportPhoto {
  id: string;
  file_name: string;
  file_url: string;
  uploaded_at: string;
}

export interface ResolutionPhoto {
  id: string;
  file_url: string;
  uploaded_at: string;
}

export interface ReportResolution {
  id: string;
  comment: string;
  resolved_at: string;
  photos: ResolutionPhoto[];
}

export interface ReportCreatedBy {
  email: string;
  username: string;
  id: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface ReportDetails {
  id: string;
  title: string;
  description: string;
  issue_type: IssueType;
  location: {
    type: string;
    coordinates: [number, number]; // [lng, lat]
  };
  status: ReportStatus;
  created_by: ReportCreatedBy;
  assigned_to?: ReportCreatedBy | null;
  resolution?: ReportResolution | null;
  created_at: string;
  updated_at: string;
  photos: ReportPhoto[];
  user_vote: 'confirm' | 'dismiss' | null;
}

export interface VoteReportBody {
  vote_type: 'confirm' | 'dismiss';
  user_location_lng: number;
  user_location_lat: number;
  accuracy: number;
}

export interface VoteReportResponse {
  id: string;
  report_id: string;
  vote_type: 'confirm' | 'dismiss';
  is_verified: boolean;
  created_at: string;
}

export interface UpdateReportBody {
  title?: string;
  description?: string;
  status?: string;
  assigned_to_id?: string;
}

@Injectable({
  providedIn: 'root',
})
export class MapWidgetApiService {
  private readonly http = inject(HttpClient);

  getGovOrgs(): Observable<ReportCreatedBy[]> {
    const params = new HttpParams().set('limit', '100');
    return this.http
      .get<
        ApiResponseSuccess<PaginatedResponse<ReportCreatedBy>>
      >(`${environment.apiUrl}/api/users/admin/users`, { params, withCredentials: true })
      .pipe(
        map((res) =>
          res.data.items.filter((u: ReportCreatedBy) => u.role === 'gov_org'),
        ),
      );
  }

  getNearbyReports(): Observable<Report[] | null> {
    return this.http
      .get<ReportsResponse>(`${environment.apiUrl}/api/reports`)
      .pipe(map((res) => (res.status === 'success' ? res.data.items : null)));
  }

  getReportById(reportId: string): Observable<ReportDetails> {
    return this.http
      .get<
        ApiResponseSuccess<ReportDetails>
      >(`${environment.apiUrl}/api/reports/${reportId}`, { withCredentials: true })
      .pipe(map((res) => res.data));
  }

  voteForReport(
    reportId: string,
    body: VoteReportBody,
  ): Observable<VoteReportResponse> {
    return this.http
      .post<
        ApiResponseSuccess<VoteReportResponse>
      >(`${environment.apiUrl}/api/votes/reports/${reportId}`, body, { withCredentials: true })
      .pipe(map((res) => res.data));
  }

  removeReportVote(reportId: string): Observable<void> {
    return this.http.delete<void>(
      `${environment.apiUrl}/api/votes/reports/${reportId}`,
      { withCredentials: true },
    );
  }

  loadAddress(lat: number, lng: number): Observable<{ display_name?: string }> {
    const url = 'https://nominatim.openstreetmap.org/reverse';

    return this.http.get<{ display_name?: string }>(url, {
      params: {
        format: 'jsonv2',
        lat,
        lon: lng,
        'accept-language': 'ru',
      },
    });
  }

  createComplaint(
    formData: FormData,
  ): Observable<ApiResponseSuccess<{ id: string }>> {
    return this.http.post<ApiResponseSuccess<{ id: string }>>(
      `${environment.apiUrl}/api/reports`,
      formData,
      { withCredentials: true },
    );
  }

  updateReport(
    reportId: string,
    body: UpdateReportBody,
  ): Observable<ReportDetails> {
    return this.http
      .put<
        ApiResponseSuccess<ReportDetails>
      >(`${environment.apiUrl}/api/reports/${reportId}`, body, { withCredentials: true })
      .pipe(map((res) => res.data));
  }

  deleteReport(reportId: string): Observable<void> {
    return this.http.delete<void>(
      `${environment.apiUrl}/api/reports/${reportId}`,
      { withCredentials: true },
    );
  }
}
