import {HttpErrorResponse, HttpInterceptorFn} from '@angular/common/http';
import {inject} from '@angular/core';
import {Router} from '@angular/router';
import {catchError, throwError} from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('token');
  const router = inject(Router);
  const authed = token ? req.clone({setHeaders: {Authorization: `Bearer ${token}`}}) : req;
  return next(authed).pipe(catchError((error: HttpErrorResponse) => {
    if (error.status === 401 && !req.url.includes('/auth/login')) {
      localStorage.removeItem('token');
      router.navigateByUrl('/login');
    }
    return throwError(() => error);
  }));
};
