import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {AuthService} from '../../core/auth.service';
import {ToastService} from '../../core/toast.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <h1>Notifications</h1>
    <p class="lead">WhatsApp updates queued for customers who opted in</p>
    <div class="card">
      <div class="row">
        <select class="input" [(ngModel)]="status" name="status">
          <option value="">All</option>
          <option value="SENT">SENT</option>
          <option value="QUEUED">QUEUED</option>
          <option value="FAILED">FAILED</option>
        </select>
        <input class="input" type="date" [(ngModel)]="createdFrom" name="from">
        <input class="input" type="date" [(ngModel)]="createdTo" name="to">
        <button class="btn secondary" type="button" (click)="load()">Filter</button>
      </div>
      <p class="muted" *ngIf="loading">Loading notifications…</p>
      <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
      <div class="empty" *ngIf="!loading && !error && !rows.length">No notifications found.</div>
      <div class="table-wrap" *ngIf="rows.length">
        <table>
          <tr><th>Type</th><th>Customer</th><th>Order</th><th>Channel</th><th>Status</th><th>Created</th><th>Sent</th><th>Failure</th><th></th></tr>
          <tr *ngFor="let note of rows">
            <td>{{note.notification_type}}</td>
            <td><a [routerLink]="['/customers', note.customer_id]">{{note.customer_name}}</a></td>
            <td><a *ngIf="note.order_id" [routerLink]="['/orders', note.order_id]">{{note.order_number}}</a></td>
            <td>{{note.channel}}</td>
            <td><span class="badge" [ngClass]="note.status.toLowerCase()">{{note.status}}</span></td>
            <td>{{note.created_at | date:'short'}}</td>
            <td>{{note.sent_at ? (note.sent_at | date:'short') : '—'}}</td>
            <td>{{note.error || '—'}}</td>
            <td><button class="btn secondary" type="button" *ngIf="auth.role()==='ADMIN' && note.status==='FAILED'" (click)="retry(note)">Retry</button></td>
          </tr>
        </table>
      </div>
    </div>
  `
})
export class NotificationsComponent {
  api = inject(ApiService);
  auth = inject(AuthService);
  toast = inject(ToastService);
  rows: any[] = [];
  status = '';
  createdFrom = '';
  createdTo = '';
  loading = true;
  error = '';
  constructor() { this.load(); }
  load() {
    this.loading = true;
    this.error = '';
    const query = new URLSearchParams({page_size: '50'});
    if (this.status) query.set('status', this.status);
    if (this.createdFrom) query.set('created_from', this.createdFrom);
    if (this.createdTo) query.set('created_to', this.createdTo);
    this.api.get<any>('/notifications?' + query.toString()).subscribe({
      next: (page) => { this.rows = page.items; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  retry(note: any) {
    this.api.post('/notifications/' + note.id + '/retry', {}).subscribe({
      next: () => { this.toast.show('Notification retried'); this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
}
