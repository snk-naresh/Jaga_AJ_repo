import {Injectable, inject} from '@angular/core';
import {Router} from '@angular/router';
import {tap} from 'rxjs';
import {ApiService} from './api.service';

@Injectable({providedIn: 'root'})
export class AuthService {
  api = inject(ApiService);
  router = inject(Router);

  login(username: string, password: string) {
    return this.api.post<any>('/auth/login', {username, password}).pipe(tap((result) => localStorage.setItem('token', result.access_token)));
  }

  logout() {
    localStorage.removeItem('token');
    this.router.navigateByUrl('/login');
  }

  isLoggedIn() { return !!localStorage.getItem('token'); }

  role() {
    const token = localStorage.getItem('token');
    if (!token) return '';
    try { return JSON.parse(atob(token.split('.')[1])).role || ''; } catch { return ''; }
  }
}
