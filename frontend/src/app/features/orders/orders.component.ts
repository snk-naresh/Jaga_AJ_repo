import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {moveSuggest, suggestNav} from '../../core/suggest-keys';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="row" style="justify-content:space-between">
      <div><h1>Orders</h1><p class="lead">Search by order number, customer, or phone</p></div>
      <a class="btn" routerLink="/orders/new">Create order</a>
    </div>
    <div class="card">
      <div class="row">
        <div class="suggest">
          <input class="input" [(ngModel)]="q" name="q" placeholder="Order, customer, or phone" autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="open" (ngModelChange)="suggest()" (focus)="suggest()" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, matches, pick, closeList)">
          <ul class="suggest-list" role="listbox" *ngIf="open && matches.length">
            <li *ngFor="let customer of matches; let i = index">
              <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="pick(customer)">
                {{customer.name}}
                <small>{{customer.phone}}<span *ngIf="customer.alternate_phone"> · {{customer.alternate_phone}}</span></small>
              </button>
            </li>
          </ul>
        </div>
        <select class="input" style="flex:1" [(ngModel)]="status" name="status">
          <option value="">Status List</option>
          <option *ngFor="let item of statuses" [value]="item">{{item}}</option>
        </select>
        <select class="input" style="flex:1" [(ngModel)]="sort" name="sort">
          <option value="created_desc">Newest</option>
          <option value="created_asc">Oldest</option>
          <option value="expected">Expected date</option>
          <option value="status">Status</option>
        </select>
        <input class="input" type="date" [(ngModel)]="createdFrom" name="from" aria-label="Created from" (ngModelChange)="page=1; load()">
        <input class="input" type="date" [(ngModel)]="createdTo" name="to" aria-label="Created to" (ngModelChange)="page=1; load()">
        <button class="btn secondary" type="button" (click)="page=1; load()">Search</button>
      </div>
      <p class="muted" *ngIf="loading">Loading orders…</p>
      <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
      <div class="empty" *ngIf="!loading && !error && !rows.length && dateFiltered">No records found</div>
      <div class="empty" *ngIf="!loading && !error && !rows.length && !dateFiltered">No orders yet. Create an order to start tracking jewellery work.</div>
      <div class="table-wrap" *ngIf="rows.length">
        <table>
          <tr><th>Order</th><th>Customer</th><th>Phone</th><th>Items</th><th>Status</th><th>Expected</th><th>Created</th><th></th></tr>
          <tr *ngFor="let order of rows">
            <td><a [routerLink]="['/orders', order.id]">{{order.order_number}}</a></td>
            <td><a [routerLink]="['/customers', order.customer_id]">{{order.customer_name}}</a></td>
            <td>{{order.customer_phone}}</td>
            <td>{{order.items.length}}</td>
            <td><span class="badge" [ngClass]="order.status.toLowerCase()">{{order.status}}</span></td>
            <td>{{order.expected_delivery_date || '—'}}</td>
            <td>{{order.created_at | date:'mediumDate'}}</td>
            <td><a [routerLink]="['/orders', order.id]">View</a></td>
          </tr>
        </table>
      </div>
      <div class="row" style="margin-top:10px" *ngIf="total>pageSize">
        <button class="btn secondary" type="button" [disabled]="page===1" (click)="page=page-1; load()">Previous</button>
        <span class="muted">{{total}} orders</span>
        <button class="btn secondary" type="button" [disabled]="page*pageSize>=total" (click)="page=page+1; load()">Next</button>
      </div>
    </div>
  `
})
export class OrdersComponent {
  api = inject(ApiService);
  q = '';
  status = '';
  sort = 'created_desc';
  createdFrom = '';
  createdTo = '';
  rows: any[] = [];
  total = 0;
  page = 1;
  pageSize = 20;
  loading = true;
  error = '';
  statuses = ['OPEN', 'IN_PROGRESS', 'READY', 'DELIVERED', 'CANCELLED'];
  matches: any[] = [];
  open = false;
  nav = suggestNav();
  moveSuggest = moveSuggest;
  pick = (customer: any) => this.choose(customer);
  closeList = () => { this.open = false; this.nav.active = -1; };
  private suggestTimer: any;
  private skipSuggest = false;
  private searched = false;
  dateFiltered = false;
  constructor() { this.load(); }
  suggest() {
    if (this.skipSuggest) { this.skipSuggest = false; return; }
    clearTimeout(this.suggestTimer);
    const term = this.q.trim();
    if (term.length < 1) {
      this.matches = [];
      this.open = false;
      this.nav.active = -1;
      if (this.searched) { this.page = 1; this.load(); }
      return;
    }
    this.suggestTimer = setTimeout(() => {
      this.api.get<any>('/customers?page_size=8&q=' + encodeURIComponent(term)).subscribe({
        next: (page) => { this.nav.active = -1; this.matches = page.items || []; this.open = this.matches.length > 0; }
      });
    }, 180);
  }
  choose(customer: any) {
    this.skipSuggest = true;
    this.q = customer.name;
    this.open = false;
    this.page = 1;
    this.load();
  }
  hideSoon() { setTimeout(() => this.open = false, 160); }
  load() {
    this.loading = true;
    this.error = '';
    this.searched = !!this.q.trim();
    this.dateFiltered = !!(this.createdFrom || this.createdTo);
    const query = new URLSearchParams({page: String(this.page), page_size: String(this.pageSize), sort: this.sort});
    if (this.q.trim()) query.set('q', this.q.trim());
    if (this.status) query.set('status', this.status);
    if (this.createdFrom) query.set('created_from', this.createdFrom);
    if (this.createdTo) query.set('created_to', this.createdTo);
    this.api.get<any>('/orders?' + query.toString()).subscribe({
      next: (page) => { this.rows = page.items; this.total = page.total; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
}
