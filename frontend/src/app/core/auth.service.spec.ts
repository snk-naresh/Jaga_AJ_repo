import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {provideRouter, Router} from '@angular/router';
import {AuthService} from './auth.service';

function token(role: string) {
  const payload = btoa(JSON.stringify({role}));
  return `header.${payload}.sig`;
}

describe('AuthService', () => {
  let auth: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([{path: 'login', children: []}])]
    });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('stores the token after a successful login', () => {
    auth.login('admin', 'secret').subscribe();
    http.expectOne('/api/auth/login').flush({access_token: token('ADMIN')});
    expect(auth.isLoggedIn()).toBe(true);
    expect(auth.role()).toBe('ADMIN');
  });

  it('clears the session and opens the sign-in page', () => {
    localStorage.setItem('token', token('STAFF'));
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, 'navigateByUrl');
    auth.logout();
    expect(auth.isLoggedIn()).toBe(false);
    expect(navigate).toHaveBeenCalledWith('/login');
  });
});
