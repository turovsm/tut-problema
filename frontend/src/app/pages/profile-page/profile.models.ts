import { IssueType } from "../../core/models/issue-type";

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  role: 'user' | 'moderator' | 'gov_org';
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface ReportLocation {
  type: 'Point';
  coordinates: [number, number]; // [lng, lat]
}

export interface ReportPhoto {
  id: string;
  file_name: string;
  file_url: string;
  uploaded_at: string;
}

export interface MyReport {
  id: string;
  title: string;
  description: string | null;
  issue_type: IssueType;
  location: ReportLocation;
  status: 'pending' | 'confirmed' | 'dismissed' | 'resolved';
  created_by: UserProfile;
  created_at: string;
  updated_at: string;
  photos: ReportPhoto[];
  user_vote: unknown | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message: string | null;
}
