import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {digitsOnly, PHONE_HINT, validIndianMobile} from '../../core/phones';
import {AuthService} from '../../core/auth.service';
import {ToastService} from '../../core/toast.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <p class="muted" *ngIf="loading">Loading customer…</p>
    <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
    <ng-container *ngIf="profile as p">
      <h1>{{p.customer.name}}</h1>
      <p class="lead">{{p.customer.phone}} · WhatsApp {{p.customer.whatsapp_opt_in ? 'opted in' : 'not opted in'}}</p>
      <section class="grid">
        <article class="card kpi"><span>Total orders</span><b>{{p.total_orders}}</b></article>
        <article class="card kpi"><span>Open</span><b>{{p.open_orders}}</b></article>
        <article class="card kpi"><span>Ready</span><b>{{p.ready_orders}}</b></article>
        <article class="card kpi"><span>Completed</span><b>{{p.completed_orders}}</b></article>
      </section>
      <div class="actions" style="margin:14px 0">
        <button class="btn secondary" type="button" *ngIf="auth.role()==='ADMIN' || !validIndianMobile(p.customer.phone)" (click)="editing=!editing">{{validIndianMobile(p.customer.phone) ? 'Edit customer' : 'Edit'}}</button>
        <a class="btn" [routerLink]="['/orders/new']" [queryParams]="{customer: p.customer.id}">Create order</a>
      </div>
      <form class="card" *ngIf="editing" (ngSubmit)="save()">
        <div class="row">
          <label class="field" style="flex:1" *ngIf="auth.role()==='ADMIN'">Name<input class="input" [(ngModel)]="form.name" name="name" required></label>
          <label class="field" style="flex:1">Mobile
            <input class="input" [ngModel]="form.phone" (ngModelChange)="form.phone = digitsOnly($event)" name="phone" required inputmode="numeric" maxlength="10">
            <span class="phone-hint" *ngIf="!validIndianMobile(form.phone)">{{phoneHint}}</span>
          </label>
          <label class="field" style="flex:1" *ngIf="auth.role()==='ADMIN'">Alternate<input class="input" [(ngModel)]="form.alternate_phone" name="alt"></label>
        </div>
        <div class="row" style="margin-top:10px" *ngIf="auth.role()==='ADMIN'">
          <label class="field" style="flex:1">Email<input class="input" [(ngModel)]="form.email" name="email"></label>
          <label class="field" style="flex:2">Address<input class="input" [(ngModel)]="form.address" name="address"></label>
        </div>
        <label *ngIf="auth.role()==='ADMIN'" style="display:block;margin:10px 0"><input type="checkbox" [(ngModel)]="form.whatsapp_opt_in" name="opt"> WhatsApp</label>
        <textarea *ngIf="auth.role()==='ADMIN'" class="input" [(ngModel)]="form.notes" name="notes" rows="3" placeholder="Notes"></textarea>
        <button class="btn" style="margin-top:10px" type="submit">Save</button>
      </form>
      <article class="card" style="margin-top:12px">
        <h2>Order history</h2>
        <div class="empty" *ngIf="!p.orders.length">No orders yet. Create an order to start tracking jewellery work.</div>
        <div class="table-wrap" *ngIf="p.orders.length">
          <table>
            <tr><th>Order</th><th>Status</th><th>Items</th><th>Expected</th></tr>
            <tr *ngFor="let order of p.orders">
              <td><a [routerLink]="['/orders', order.id]">{{order.order_number}}</a></td>
              <td><span class="badge" [ngClass]="order.status.toLowerCase()">{{order.status}}</span></td>
              <td>{{order.items.length}}</td>
              <td>{{order.expected_delivery_date || '—'}}</td>
            </tr>
          </table>
        </div>
      </article>
    </ng-container>
  `
})
export class CustomerDetailComponent {
  api = inject(ApiService);
  auth = inject(AuthService);
  route = inject(ActivatedRoute);
  toast = inject(ToastService);
  profile: any = null;
  form: any = {};
  loading = true;
  error = '';
  editing = false;
  phoneHint = PHONE_HINT;
  digitsOnly = digitsOnly;
  validIndianMobile = validIndianMobile;
  constructor() { this.load(); }
  load() {
    const id = this.route.snapshot.paramMap.get('id');
    this.loading = true;
    this.api.get<any>('/customers/' + id + '/profile').subscribe({
      next: (profile) => { this.profile = profile; this.form = {...profile.customer}; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  save() {
    if (!String(this.form.name || '').trim() || !validIndianMobile(this.form.phone)) return;
    const body = this.auth.role() === 'ADMIN' || validIndianMobile(this.profile.customer.phone) ? this.form : {phone: this.form.phone};
    this.api.patch('/customers/' + this.profile.customer.id, body).subscribe({
      next: () => { this.toast.show('Customer updated'); this.editing = false; this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
}
