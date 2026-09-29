import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {digitsOnly, PHONE_HINT, validIndianMobile} from '../../core/phones';
import {moveSuggest, suggestNav} from '../../core/suggest-keys';
import {ToastService} from '../../core/toast.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  styles: [`
    .sheet { margin-top: 12px; }
    .sheet h2 { margin: 0; font-size: 20px; }
    .sheet-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px; }
    .sheet .suggest { min-width: 0; }
    .wide { grid-column: 1 / -1; }
    .check { display: flex; align-items: center; gap: 8px; margin: 14px 0; }
    .btn.highlight {
      background: linear-gradient(180deg, #fff4cc, #e0b34a);
      color: #1a1406;
      box-shadow: 0 0 0 1px #f6de9a, 0 8px 22px rgba(224, 179, 74, 0.5);
    }
    .btn.dim {
      background: transparent;
      color: #8ea4c4;
      border: 1px solid rgba(142, 164, 196, 0.28);
      box-shadow: none;
      opacity: 0.55;
      font-weight: 500;
    }
    @media (max-width: 700px) { .sheet-grid { grid-template-columns: 1fr; } }
  `],
  template: `
    <div class="row" style="justify-content:space-between">
      <div><h1>Customers</h1><p class="lead">Search by name or mobile number</p></div>
      <button class="btn" type="button" (click)="showForm=!showForm">Add customer</button>
    </div>
    <form class="card sheet" *ngIf="showForm" (ngSubmit)="add()">
      <h2>New customer</h2>
      <p class="muted">Name and mobile are required. A matching name opens the existing record.</p>
      <div class="sheet-grid">
        <label class="field suggest">Name
          <input class="input" [(ngModel)]="form.name" name="name" required autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="open==='name'" (ngModelChange)="suggest('name')" (focus)="suggest('name')" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, open==='name' ? matches : [], openExisting, closeList)">
          <ul class="suggest-list" role="listbox" *ngIf="open==='name' && matches.length">
            <li *ngFor="let customer of matches; let i = index">
              <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="openCustomer(customer)">
                {{customer.name}}
                <small>Already on file · {{customer.phone}}</small>
              </button>
            </li>
          </ul>
        </label>
        <label class="field suggest">Mobile
          <input class="input" [ngModel]="form.phone" (ngModelChange)="setPhone($event)" name="phone" required inputmode="numeric" maxlength="10" autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="open==='phone'" (focus)="suggest('phone')" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, open==='phone' ? matches : [], openExisting, closeList)">
          <span class="phone-hint" *ngIf="!validIndianMobile(form.phone)">{{phoneHint}}</span>
          <span class="existing" *ngIf="exactMatch() as found">existing customer · {{found.name}}</span>
          <ul class="suggest-list" role="listbox" *ngIf="open==='phone' && matches.length">
            <li *ngFor="let customer of matches; let i = index">
              <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="openCustomer(customer)">
                {{customer.name}}
                <small>existing customer · {{customer.phone}}</small>
              </button>
            </li>
          </ul>
        </label>
        <label class="field">Alternate phone
          <input class="input" [(ngModel)]="form.alternate_phone" name="alternate_phone">
        </label>
        <label class="field">Email
          <input class="input" type="email" [(ngModel)]="form.email" name="email">
        </label>
        <label class="field wide">Address
          <input class="input" [(ngModel)]="form.address" name="address">
        </label>
        <label class="field wide">Notes
          <textarea class="input" [(ngModel)]="form.notes" name="notes" rows="3"></textarea>
        </label>
      </div>
      <label class="check"><input type="checkbox" [(ngModel)]="form.whatsapp_opt_in" name="opt"> WhatsApp</label>
      <div class="actions">
        <button class="btn" type="submit">Save</button>
        <button class="btn secondary" type="button" (click)="cancel()">Cancel</button>
      </div>
    </form>
    <div class="card" style="margin-top:12px">
      <div class="row">
        <div class="suggest">
          <input class="input" [(ngModel)]="q" name="q" placeholder="Search name or phone" autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="open==='search'" (ngModelChange)="suggest('search')" (focus)="suggest('search')" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, open==='search' ? matches : [], pick, closeList)" (keyup.enter)="searchFromEnter()">
          <ul class="suggest-list" role="listbox" *ngIf="open==='search' && matches.length">
            <li *ngFor="let customer of matches; let i = index">
              <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="pick(customer)">
                {{customer.name}}
                <small>{{customer.phone}}<span *ngIf="customer.alternate_phone"> · {{customer.alternate_phone}}</span></small>
              </button>
            </li>
          </ul>
        </div>
        <button class="btn secondary" type="button" (click)="page=1; load()">Search</button>
      </div>
      <p class="muted" *ngIf="loading">Loading customers…</p>
      <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
      <div class="empty" *ngIf="!loading && !error && !rows.length">No records found <button type="button" (click)="showForm=true" style="background:none;border:0;padding:0;color:inherit;font:inherit;text-decoration:underline;cursor:pointer">Add new?</button></div>
      <div class="table-wrap" *ngIf="rows.length">
        <table>
          <tr><th>Name</th><th>Mobile</th><th>WhatsApp</th><th>Added</th><th></th></tr>
          <ng-container *ngFor="let customer of rows">
            <tr>
              <td><a [routerLink]="['/customers', customer.id]">{{customer.name}}</a></td>
              <td>
                <div *ngIf="fixingId!==customer.id">{{customer.phone}}</div>
                <div *ngIf="!validIndianMobile(customer.phone) && fixingId!==customer.id"><button class="btn secondary" type="button" (click)="startFix(customer)">Edit</button></div>
                <div *ngIf="fixingId===customer.id">
                  <input class="input" [ngModel]="fixPhone" (ngModelChange)="fixPhone=digitsOnly($event)" name="fixPhone" inputmode="numeric" maxlength="10">
                  <span class="phone-hint" *ngIf="!validIndianMobile(fixPhone)">{{phoneHint}}</span>
                  <button class="btn" type="button" (click)="saveFix(customer)">Save</button>
                </div>
              </td>
              <td>{{customer.whatsapp_opt_in ? 'Opted in' : 'No'}}</td>
              <td>{{customer.created_at | date:'mediumDate'}}</td>
              <td>
                <div class="actions">
                  <a class="btn" *ngIf="searched && latest(customer) as order" [routerLink]="['/orders', order.id]">View order</a>
                  <button class="btn" type="button" *ngIf="searched && !latest(customer)" disabled>View order</button>
                  <a class="btn dim" [routerLink]="['/orders/new']" [queryParams]="{customer: customer.id}">New order</a>
                  <button class="btn highlight" type="button" (click)="toggleHistory(customer)">History</button>
                </div>
              </td>
            </tr>
            <tr *ngIf="historyFor===customer.id">
              <td colspan="5">
                <div class="empty" *ngIf="!orders[customer.id]">Loading history…</div>
                <div class="empty" *ngIf="orders[customer.id] && !older(customer).length">No older orders.</div>
                <table *ngIf="older(customer).length">
                  <tr><th>Order</th><th>Status</th><th>Items</th><th>Expected</th><th>Created</th></tr>
                  <tr *ngFor="let order of older(customer)">
                    <td><a [routerLink]="['/orders', order.id]">{{order.order_number}}</a></td>
                    <td><span class="badge" [ngClass]="order.status.toLowerCase()">{{order.status}}</span></td>
                    <td>{{order.items.length}}</td>
                    <td>{{order.expected_delivery_date || '—'}}</td>
                    <td>{{order.created_at | date:'mediumDate'}}</td>
                  </tr>
                </table>
              </td>
            </tr>
          </ng-container>
        </table>
      </div>
      <div class="row" style="margin-top:10px" *ngIf="total>pageSize">
        <button class="btn secondary" type="button" [disabled]="page===1" (click)="page=page-1; load()">Previous</button>
        <span class="muted">Page {{page}}</span>
        <button class="btn secondary" type="button" [disabled]="page*pageSize>=total" (click)="page=page+1; load()">Next</button>
      </div>
    </div>
  `
})
export class CustomersComponent {
  api = inject(ApiService);
  toast = inject(ToastService);
  router = inject(Router);
  q = '';
  matches: any[] = [];
  open = '';
  nav = suggestNav();
  moveSuggest = moveSuggest;
  pick = (customer: any) => this.choose(customer);
  openExisting = (customer: any) => this.openCustomer(customer);
  closeList = () => { this.open = ''; this.nav.active = -1; };
  private suggestTimer: any;
  private skipSuggest = false;
  searched = false;
  orders: Record<number, any[]> = {};
  historyFor: number | null = null;
  rows: any[] = [];
  total = 0;
  page = 1;
  pageSize = 20;
  loading = true;
  error = '';
  showForm = false;
  form: any = this.blank();
  constructor() { this.load(); }
  suggest(field: string) {
    if (field === 'search' && this.skipSuggest) { this.skipSuggest = false; return; }
    clearTimeout(this.suggestTimer);
    const term = (field === 'name' ? this.form.name : field === 'phone' ? this.form.phone : this.q).trim();
    if (term.length < 1) {
      this.matches = [];
      this.open = '';
      this.nav.active = -1;
      if (field === 'search' && this.searched) { this.page = 1; this.load(); }
      return;
    }
    this.suggestTimer = setTimeout(() => {
      this.api.get<any>('/customers?page_size=8&q=' + encodeURIComponent(term)).subscribe({
        next: (page) => { this.nav.active = -1; this.matches = page.items || []; this.open = this.matches.length ? field : ''; }
      });
    }, 180);
  }
  searchFromEnter() {
    if (this.nav.picked) { this.nav.picked = false; return; }
    this.page = 1;
    this.load();
  }
  choose(customer: any) {
    this.skipSuggest = true;
    this.q = customer.name;
    this.open = '';
    this.page = 1;
    this.load();
  }
  openCustomer(customer: any) {
    this.open = '';
    this.router.navigate(['/customers', customer.id]);
  }
  hideSoon() { setTimeout(() => this.open = '', 160); }
  latest(customer: any) { return (this.orders[customer.id] || [])[0]; }
  older(customer: any) { return (this.orders[customer.id] || []).slice(1); }
  toggleHistory(customer: any) {
    if (this.historyFor === customer.id) { this.historyFor = null; return; }
    this.historyFor = customer.id;
    if (this.orders[customer.id]) return;
    this.api.get<any>('/orders?page_size=50&sort=created_desc&customer_id=' + customer.id).subscribe({
      next: (result) => { this.orders[customer.id] = result.items || []; },
      error: () => { this.orders[customer.id] = []; }
    });
  }
  load() {
    this.loading = true;
    this.error = '';
    this.searched = !!this.q.trim();
    const query = new URLSearchParams({page: String(this.page), page_size: String(this.pageSize)});
    if (this.q.trim()) query.set('q', this.q.trim());
    this.api.get<any>('/customers?' + query.toString()).subscribe({
      next: (page) => {
        this.rows = page.items;
        this.total = page.total;
        this.orders = {};
        this.historyFor = null;
        if (!this.searched || !this.rows.length) { this.loading = false; return; }
        let pending = this.rows.length;
        for (const customer of this.rows) {
          this.api.get<any>('/orders?page_size=50&sort=created_desc&customer_id=' + customer.id).subscribe({
            next: (result) => { this.orders[customer.id] = result.items || []; if (--pending === 0) this.loading = false; },
            error: () => { this.orders[customer.id] = []; if (--pending === 0) this.loading = false; }
          });
        }
      },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  phoneHint = PHONE_HINT;
  validIndianMobile = validIndianMobile;
  digitsOnly = digitsOnly;
  fixingId: number | null = null;
  fixPhone = '';
  exactMatch() {
    return this.matches.find((customer) => customer.phone === this.form.phone) || null;
  }
  startFix(customer: any) {
    this.fixingId = customer.id;
    this.fixPhone = digitsOnly(customer.phone || '');
  }
  saveFix(customer: any) {
    if (!validIndianMobile(this.fixPhone)) return;
    this.api.patch('/customers/' + customer.id, {phone: this.fixPhone}).subscribe({
      next: () => { this.toast.show('Phone saved'); this.fixingId = null; this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
  setPhone(value: string) {
    this.form.phone = digitsOnly(value);
    this.suggest('phone');
  }
  blank() { return {name: '', phone: '', alternate_phone: '', email: '', address: '', notes: '', whatsapp_opt_in: false}; }
  cancel() {
    this.form = this.blank();
    this.showForm = false;
    this.open = '';
    this.matches = [];
  }
  add() {
    if (!String(this.form.name || '').trim() || !validIndianMobile(this.form.phone) || this.exactMatch()) return;
    this.api.post('/customers', this.form).subscribe({
      next: () => { this.toast.show('Customer saved'); this.form = this.blank(); this.showForm = false; this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
}
