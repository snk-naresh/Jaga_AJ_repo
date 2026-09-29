import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ApiService, apiMessage} from '../../core/api.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <h1>Reports</h1>
    <p class="lead">Orders, customers, and WhatsApp results for the selected dates</p>
    <div class="card">
      <div class="row">
        <button class="btn secondary" type="button" *ngFor="let item of presets" (click)="preset=item.id; load()">{{item.label}}</button>
      </div>
      <div class="row" *ngIf="preset==='custom'" style="margin-top:10px">
        <input class="input" type="date" [(ngModel)]="start" name="start">
        <input class="input" type="date" [(ngModel)]="end" name="end">
        <button class="btn" type="button" (click)="load()">Apply</button>
      </div>
      <p class="muted" *ngIf="loading">Loading report…</p>
      <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
      <ng-container *ngIf="data as report">
        <p class="muted">{{report.start}} to {{report.end}}</p>
        <section class="grid">
          <article class="card kpi"><span>Pending orders</span><b>{{report.pending_orders}}</b></article>
          <article class="card kpi"><span>Ready orders</span><b>{{report.ready_orders}}</b></article>
          <article class="card kpi"><span>Delivered</span><b>{{report.delivered_orders}}</b></article>
          <article class="card kpi"><span>Repeat customers</span><b>{{report.repeat_customers}}</b></article>
        </section>
        <div class="split" style="margin-top:12px">
          <article class="card">
            <h2>Orders by status</h2>
            <div class="empty" *ngIf="!statusRows(report).length">No orders in this range.</div>
            <div class="bars">
              <div class="bar" *ngFor="let row of statusRows(report)"><em>{{row.label}}</em><span><i [style.width.%]="row.pct"></i></span><b>{{row.count}}</b></div>
            </div>
          </article>
          <article class="card">
            <h2>Notifications</h2>
            <p>Sent {{report.notifications.sent}}</p>
            <p>Queued {{report.notifications.queued}}</p>
            <p>Failed {{report.notifications.failed}}</p>
            <h2>New customers</h2>
            <p>{{report.new_customers}}</p>
          </article>
        </div>
      </ng-container>
    </div>
  `
})
export class ReportsComponent {
  api = inject(ApiService);
  presets = [
    {id: 'today', label: 'Today'},
    {id: '7d', label: 'Last 7 days'},
    {id: '30d', label: 'Last 30 days'},
    {id: 'month', label: 'This month'},
    {id: 'custom', label: 'Custom range'}
  ];
  preset = '30d';
  start = '';
  end = '';
  data: any = null;
  loading = true;
  error = '';
  constructor() { this.load(); }
  load() {
    this.loading = true;
    this.error = '';
    const query = new URLSearchParams({preset: this.preset});
    if (this.preset === 'custom') {
      if (!this.start || !this.end) { this.loading = false; return; }
      query.set('start', this.start);
      query.set('end', this.end);
    }
    this.api.get<any>('/reports?' + query.toString()).subscribe({
      next: (data) => { this.data = data; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  statusRows(report: any) {
    const rows = Object.entries(report.orders_by_status || {}).map(([label, count]) => ({label, count: Number(count)}));
    const max = Math.max(1, ...rows.map((row) => row.count));
    return rows.map((row) => ({...row, pct: Math.round((row.count / max) * 100)}));
  }
}
