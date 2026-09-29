import {TestBed} from '@angular/core/testing';
import {provideHttpClient} from '@angular/common/http';
import {HttpTestingController, provideHttpClientTesting} from '@angular/common/http/testing';
import {provideRouter} from '@angular/router';
import {LoginComponent} from './login.component';

describe('LoginComponent', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])]
    }).compileComponents();
  });

  it('shows the sign-in form', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Sign in');
    expect(text).toContain('Anand Jewellers');
  });

  it('shows the API message when sign-in fails', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
    fixture.componentInstance.username = 'admin';
    fixture.componentInstance.password = 'wrong';
    fixture.componentInstance.submit();
    const http = TestBed.inject(HttpTestingController);
    http.expectOne('/api/auth/login').flush({detail: 'Invalid username or password'}, {status: 401, statusText: 'Unauthorized'});
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Invalid username or password');
    http.verify();
  });
});
