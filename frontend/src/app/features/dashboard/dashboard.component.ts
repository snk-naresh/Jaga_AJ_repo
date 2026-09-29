import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {moveSuggest, suggestNav} from '../../core/suggest-keys';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="row" style="justify-content:space-between">
      <div><h1>Dashboard</h1><p class="lead">This month starts from zero. Asking for a month saves those figures.</p></div>
      <label class="field">Month<input class="input" type="month" [(ngModel)]="month" (ngModelChange)="load()"></label>
      <button class="btn secondary" type="button" (click)="load()">Refresh</button>
    </div>
    <p class="muted" *ngIf="loading">Loading dashboard…</p>
    <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
    <p class="muted" *ngIf="data?.saved_at">Saved for {{data.month}} at {{data.saved_at | date:'medium'}}</p>
    <ng-container *ngIf="data as d">
      <section class="grid">
        <article class="card kpi"><span>Total customers</span><b>{{d.total_customers}}</b></article>
        <article class="card kpi"><span>Total orders</span><b>{{d.total_orders}}</b></article>
        <article class="card kpi"><span>Open orders</span><b>{{d.open_orders}}</b></article>
        <article class="card kpi"><span>Ready orders</span><b>{{d.ready_orders}}</b></article>
        <article class="card kpi"><span>Delivered</span><b>{{d.delivered_orders}}</b></article>
        <article class="card kpi"><span>Pending items</span><b>{{d.pending_items}}</b></article>
        <article class="card kpi"><span>Ready items</span><b>{{d.ready_items}}</b></article>
        <article class="card kpi"><span>WhatsApp queued / failed</span><b>{{d.notifications_queued}} / {{d.notifications_failed}}</b></article>
      </section>
      <section class="split" style="margin-top:14px">
        <article class="card">
          <h2>Recent orders</h2>
          <div class="empty" *ngIf="!d.recent_orders.length">No orders yet. Create an order to start tracking jewellery work.</div>
          <div class="table-wrap" *ngIf="d.recent_orders.length">
            <table>
              <tr><th>Order</th><th>Customer</th><th>Status</th><th>Items</th></tr>
              <tr *ngFor="let order of d.recent_orders">
                <td><a [routerLink]="['/orders', order.id]">{{order.order_number}}</a></td>
                <td>{{order.customer_name}}</td>
                <td><span class="badge" [ngClass]="order.status.toLowerCase()">{{order.status}}</span></td>
                <td>{{order.items.length}}</td>
              </tr>
            </table>
          </div>
          <h2 style="margin-top:18px">Orders created</h2>
          <div class="bars">
            <div class="bar" *ngFor="let day of d.orders_by_day">
              <em>{{day.date.slice(5)}}</em><span><i [style.width.%]="width(day.count)"></i></span><b>{{day.count}}</b>
            </div>
          </div>
        </article>
        <div>
          <article class="card">
            <h2>Quick actions</h2>
            <div class="suggest" style="width:100%; margin-bottom:12px">
              <input class="input" [(ngModel)]="q" name="customerSearch" placeholder="Search customer by name or mobile" autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="open" (ngModelChange)="suggest()" (focus)="suggest()" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, matches, pick, closeList)">
              <ul class="suggest-list" role="listbox" *ngIf="open && matches.length">
                <li *ngFor="let customer of matches; let i = index">
                  <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="pick(customer)">
                    {{customer.name}}
                    <small>{{customer.phone}}<span *ngIf="customer.alternate_phone"> · {{customer.alternate_phone}}</span></small>
                  </button>
                </li>
              </ul>
            </div>
            <div class="actions">
              <a class="btn" routerLink="/customers">Add customer</a>
              <a class="btn gold" routerLink="/orders/new">Create order</a>
              <a class="btn secondary" routerLink="/orders">View orders</a>
            </div>
          </article>
          <article class="card" style="margin-top:12px">
            <h2>Status summary</h2>
            <div class="bars">
              <div class="bar" *ngFor="let row of statusRows(d)"><em>{{row.label}}</em><span><i [style.width.%]="row.pct"></i></span><b>{{row.count}}</b></div>
            </div>
          </article>
          <article class="card" style="margin-top:12px">
            <h2>Recent customers</h2>
            <div class="empty" *ngIf="!d.recent_customers.length">No records found <a routerLink="/customers">Add new?</a></div>
            <p *ngFor="let customer of d.recent_customers"><a [routerLink]="['/customers', customer.id]">{{customer.name}}</a><br><span class="muted">{{customer.phone}}</span></p>
          </article>
        </div>
      </section>
    </ng-container>
  `
})
export class DashboardComponent {
  api = inject(ApiService);
  router = inject(Router);
  data: any = null;
  q = '';
  matches: any[] = [];
  open = false;
  nav = suggestNav();
  moveSuggest = moveSuggest;
  pick = (customer: any) => this.choose(customer);
  closeList = () => { this.open = false; this.nav.active = -1; };
  private suggestTimer: any;
  loading = true;
  error = '';
  month = '';
  constructor() {
    const now = new Date();
    this.month = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');
    this.load();
  }
  suggest() {
    clearTimeout(this.suggestTimer);
    const term = this.q.trim();
    if (term.length < 1) { this.matches = []; this.open = false; this.nav.active = -1; return; }
    this.suggestTimer = setTimeout(() => {
      this.api.get<any>('/customers?page_size=8&q=' + encodeURIComponent(term)).subscribe({
        next: (page) => { this.nav.active = -1; this.matches = page.items || []; this.open = this.matches.length > 0; }
      });
    }, 180);
  }
  choose(customer: any) {
    this.open = false;
    this.router.navigate(['/customers', customer.id]);
  }
  hideSoon() { setTimeout(() => this.open = false, 160); }
  load() {
    this.loading = true;
    this.error = '';
    this.api.get<any>('/dashboard?month=' + encodeURIComponent(this.month)).subscribe({
      next: (data) => { this.data = data; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  width(count: number) {
    const max = Math.max(1, ...(this.data?.orders_by_day || []).map((day: any) => day.count));
    return Math.round((count / max) * 100);
  }
  statusRows(data: any) {
    const rows = Object.entries(data.status_distribution || {}).map(([label, count]) => ({label, count: Number(count)}));
    const max = Math.max(1, ...rows.map((row) => row.count));
    return rows.map((row) => ({...row, pct: Math.round((row.count / max) * 100)}));
  }
}
