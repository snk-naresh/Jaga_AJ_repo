import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {RouterLink, RouterLinkActive, RouterOutlet} from '@angular/router';
import {AuthService} from './core/auth.service';
import {ToastService} from './core/toast.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="shell">
      <header class="top" *ngIf="auth.isLoggedIn()">
        <div class="brand">Anand <span>Jewellers</span></div>
        <button class="menu" type="button" (click)="open = !open">Menu</button>
        <nav class="nav" [class.open]="open">
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{exact:true}" (click)="open=false">Dashboard</a>
          <a routerLink="/customers" routerLinkActive="active" (click)="open=false">Customers</a>
          <a routerLink="/orders" routerLinkActive="active" (click)="open=false">Orders</a>
          <a routerLink="/inventory" routerLinkActive="active" (click)="open=false">Inventory</a>
          <a routerLink="/notifications" routerLinkActive="active" (click)="open=false">Notifications</a>
          <a routerLink="/reports" routerLinkActive="active" (click)="open=false">Reports</a>
          <a routerLink="/settings" routerLinkActive="active" (click)="open=false">Settings</a>
          <a routerLink="/security" routerLinkActive="active" *ngIf="auth.role()==='ADMIN'" (click)="open=false">Security</a>
          <button class="logout" type="button" (click)="auth.logout()">Logout</button>
        </nav>
      </header>
      <main class="content"><router-outlet/></main>
      <div class="toast" *ngIf="toast.text()">{{toast.text()}}</div>
    </div>
  `
})
export class AppComponent {
  auth = inject(AuthService);
  toast = inject(ToastService);
  open = false;
}
