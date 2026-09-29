import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {AuthService} from '../../core/auth.service';
import {ToastService} from '../../core/toast.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <p class="muted" *ngIf="loading">Loading order…</p>
    <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
    <ng-container *ngIf="order as current">
      <h1>{{current.order_number}}</h1>
      <p class="lead"><a [routerLink]="['/customers', current.customer_id]">{{current.customer_name}}</a> · {{current.customer_phone}} · WhatsApp {{current.whatsapp_opt_in ? 'opted in' : 'not opted in'}}</p>
      <div class="timeline">
        <div *ngFor="let step of steps" [class.on]="reached(current.status, step)"><i></i>{{step}}</div>
      </div>
      <div class="split">
        <article class="card">
          <h2>Items</h2>
          <div class="card" style="margin-bottom:10px" *ngFor="let item of current.items">
            <div class="row" style="justify-content:space-between">
              <div><b>{{item.item_type}}</b> · {{item.item_code}}<div class="muted">{{item.description || 'No description'}} · Qty {{item.quantity}}</div></div>
              <span class="badge" [ngClass]="item.status.toLowerCase()">{{item.status}}</span>
            </div>
            <div class="actions" style="margin-top:8px">
              <button class="btn secondary" type="button" *ngFor="let next of item.allowed_transitions" [hidden]="auth.role()!=='ADMIN'" (click)="moveItem(item, next)">{{next}}</button>
              <button class="btn secondary" type="button" *ngIf="current.whatsapp_opt_in" (click)="notify(item)">WhatsApp</button>
              <label class="btn secondary" *ngIf="auth.role()==='ADMIN'">Photo<input type="file" accept="image/png,image/jpeg,image/webp" hidden (change)="upload(item, $event)"></label>
            </div>
            <img *ngIf="photos[item.id]" [src]="photos[item.id]" alt="" style="max-width:180px;margin-top:8px;border-radius:8px">
          </div>
        </article>
        <aside>
          <article class="card">
            <h2>Order</h2>
            <p>Status <span class="badge" [ngClass]="current.status.toLowerCase()">{{current.status}}</span></p>
            <p class="muted">Created {{current.created_at | date:'medium'}}</p>
            <p class="muted">Expected {{current.expected_delivery_date || 'not set'}}</p>
            <p>{{current.notes || 'No notes'}}</p>
            <div class="actions" *ngIf="auth.role()==='ADMIN'">
              <button class="btn" type="button" *ngFor="let next of current.allowed_transitions" (click)="moveOrder(next)">Mark {{next}}</button>
            </div>
          </article>
          <article class="card" style="margin-top:12px">
            <h2>Notifications</h2>
            <div class="empty" *ngIf="!notes.length">No notifications found.</div>
            <p *ngFor="let note of notes"><span class="badge" [ngClass]="note.status.toLowerCase()">{{note.status}}</span> {{note.notification_type}}<br><span class="muted">{{note.message}}</span></p>
          </article>
        </aside>
      </div>
    </ng-container>
  `
})
export class OrderDetailComponent {
  api = inject(ApiService);
  auth = inject(AuthService);
  route = inject(ActivatedRoute);
  toast = inject(ToastService);
  order: any = null;
  notes: any[] = [];
  photos: Record<number, string> = {};
  loading = true;
  error = '';
  steps = ['OPEN', 'IN_PROGRESS', 'READY', 'DELIVERED'];
  constructor() { this.load(); }
  load() {
    const id = this.route.snapshot.paramMap.get('id');
    this.loading = true;
    this.api.get<any>('/orders/' + id).subscribe({
      next: (order) => {
        this.order = order;
        this.loading = false;
        this.api.get<any>('/notifications?order_id=' + order.id).subscribe({next: (page) => this.notes = page.items});
      },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  reached(status: string, step: string) {
    const rank: any = {OPEN: 0, IN_PROGRESS: 1, PARTIALLY_READY: 1, READY: 2, DELIVERED: 3};
    return (rank[status] ?? -1) >= rank[step];
  }
  moveItem(item: any, status: string) {
    if (status === 'CANCELLED' && !confirm('Cancel this item?')) return;
    this.api.patch('/orders/items/' + item.id + '/status', {status}).subscribe({
      next: () => { this.toast.show('Item updated'); this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
  moveOrder(status: string) {
    if ((status === 'CANCELLED' || status === 'DELIVERED') && !confirm('Update this order to ' + status + '?')) return;
    this.api.patch('/orders/' + this.order.id + '/status', {status}).subscribe({
      next: () => { this.toast.show('Order updated'); this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
  notify(item: any) {
    this.api.post('/orders/items/' + item.id + '/notify-ready', {}).subscribe({
      next: () => { this.toast.show('WhatsApp update queued'); this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
  upload(item: any, event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append('file', file);
    this.api.post<any>('/orders/items/' + item.id + '/photo', body).subscribe({
      next: (result) => { this.photos[item.id] = result.url; this.toast.show('Photo saved'); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
}
