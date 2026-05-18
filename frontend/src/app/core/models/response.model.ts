export interface ApiResponseSuccess<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

export interface ApiError {
  status: 'error' | 'success';
  error: string;
  code: number;
}
