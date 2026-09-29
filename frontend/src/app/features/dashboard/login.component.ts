import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {AuthService} from '../../core/auth.service';
import {apiMessage} from '../../core/api.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="card" style="max-width:420px;margin:48px auto">
      <p class="muted" style="letter-spacing:.14em;text-transform:uppercase;font-size:12px">Anand Jewellers</p>
      <h1>Sign in</h1>
      <p class="lead">Workshop and customer desk</p>
      <form (ngSubmit)="submit()" class="stack">
        <label class="field">Username<input class="input" [(ngModel)]="username" name="username" required></label>
        <label class="field">Password<input class="input" type="password" [(ngModel)]="password" name="password" required></label>
        <button class="btn" type="submit">Sign in</button>
        <p class="error-box" *ngIf="error">{{error}}</p>
      </form>
    </div>
  `,
  styles: [`.stack{display:grid;gap:12px}`]
})
export class LoginComponent {
  username = 'admin';
  password = '';
  error = '';
  auth = inject(AuthService);
  router = inject(Router);
  submit() {
    this.error = '';
    this.auth.login(this.username, this.password).subscribe({
      next: () => this.router.navigateByUrl('/'),
      error: (err) => this.error = apiMessage(err)
    });
  }
}
