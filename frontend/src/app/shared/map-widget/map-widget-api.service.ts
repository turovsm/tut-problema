import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ReportsResponse {
    status: "success" | "error";
    data: {
        items: [Report]
    };
    message: string;
}

export interface Report {
  id: string;
  title: string;
  description: string;
  issue_type: string;
  location: {
    type: string;
    coordinates: [number, number]; // [lng, lat]
  };
  status: string;
  created_at: string;
  updated_at: string;
  photos: string[];
  user_vote: string;
}

@Injectable({
  providedIn: 'root'
})
export class MapWidgetApiService {
  private readonly http = inject(HttpClient);

  getNearbyReports(lat=58.0, lon=56.25): Observable<Report[] | null> {
    return this.http.get<ReportsResponse>(`${environment.apiUrl}/api/reports/nearby`,
        {params: {
            lat,
            lon
        }}
    ).pipe(
      map(res => res.status === 'success' ? res.data.items : null)
    );
  }
}