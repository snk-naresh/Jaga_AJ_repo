import {Injectable, inject} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';

export function apiMessage(error: any): string {
  const detail = error?.error?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) return detail.map((item) => item?.msg || 'Invalid value').join(' ');
  return 'Something went wrong. Please try again.';
}

@Injectable({providedIn: 'root'})
export class ApiService {
  http = inject(HttpClient);
  base = '/api';
  get<T>(path: string): Observable<T> { return this.http.get<T>(this.base + path); }
  post<T>(path: string, body: any): Observable<T> { return this.http.post<T>(this.base + path, body); }
  patch<T>(path: string, body: any): Observable<T> { return this.http.patch<T>(this.base + path, body); }
  delete<T>(path: string): Observable<T> { return this.http.delete<T>(this.base + path); }
}
