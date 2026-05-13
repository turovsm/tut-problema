import { IssueType } from "./issue-type";

export type ReportStatus = 'pending' | 'confirmed' | 'dismissed' | 'resolved';

export interface ReportVoteStats {
  report_id: string;
  confirm_count: number;
  dismiss_count: number;
  current_status: ReportStatus;
}

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  role: 'user' | 'moderator' | 'gov_org';
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface MyReport {
  id: string;
  title: string;
  description: string | null;
  issue_type: IssueType;
  location: ReportLocation;
  status: ReportStatus;
  created_by: UserProfile;
  created_at: string;
  updated_at: string;
  photos: ReportPhoto[];
  user_vote: unknown | null;
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