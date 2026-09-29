import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ApiService, apiMessage} from '../../core/api.service';
import {ToastService} from '../../core/toast.service';
import {AuthService} from '../../core/auth.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="row" style="justify-content:space-between">
      <div><h1>Inventory</h1><p class="lead">Stock on hand, reserved for orders, and low-stock pieces</p></div>
      <button class="btn" type="button" (click)="show=!show">Add item</button>
    </div>
    <form class="card row" *ngIf="show" (ngSubmit)="create()">
      <input class="input" [(ngModel)]="form.sku" name="sku" placeholder="SKU" required>
      <input class="input" [(ngModel)]="form.name" name="name" placeholder="Name" required>
      <select class="input" [(ngModel)]="form.category" name="category">
        <option *ngFor="let category of categories" [value]="category">{{category}}</option>
      </select>
      <input class="input" type="number" [(ngModel)]="form.quantity" name="qty" placeholder="Quantity">
      <input class="input" [(ngModel)]="form.purity" name="purity" placeholder="Purity">
      <input class="input" [(ngModel)]="form.weight" name="weight" placeholder="Weight">
      <button class="btn" type="submit">Save</button>
    </form>
    <div class="card" style="margin-top:12px">
      <div class="row">
        <input class="input" [(ngModel)]="q" name="q" placeholder="SKU, name, or category">
        <select class="input" [(ngModel)]="category" name="filter">
          <option value="">All categories</option>
          <option *ngFor="let item of categories" [value]="item">{{item}}</option>
        </select>
        <!-- <label><input type="checkbox" [(ngModel)]="low" name="low"> Low stock</label> -->
        <button class="btn secondary" type="button" (click)="load()">Search</button>
      </div>
      <p class="muted" *ngIf="loading">Loading inventory…</p>
      <div class="error-box" *ngIf="error">{{error}} <button class="btn secondary" type="button" (click)="load()">Retry</button></div>
      <div class="empty" *ngIf="!loading && !error && !rows.length">No inventory items match this search.</div>
      <div class="table-wrap" *ngIf="rows.length">
        <table>
          <tr><th>SKU</th><th>Name</th><th>Category</th><th>On hand</th><th>Reserved</th><th>Free</th><th>Status</th><th></th></tr>
          <tr *ngFor="let item of rows">
            <td>{{item.sku}}</td>
            <td>{{item.name}}<div class="muted">{{item.purity}} {{item.weight}}</div></td>
            <td>{{item.category}}</td>
            <td>{{item.quantity}}</td>
            <td>{{item.reserved_quantity}}</td>
            <td [class.badge]="item.low_stock" [class.failed]="item.low_stock">{{item.available_quantity}}</td>
            <td>{{item.status}}</td>
            <td class="actions">
              <button class="btn secondary" type="button" *ngIf="auth.role()==='ADMIN'" (click)="adjust(item, 1)">+1</button>
              <button class="btn secondary" type="button" *ngIf="auth.role()==='ADMIN'" (click)="adjust(item, -1)">-1</button>
              <button class="btn secondary" type="button" *ngIf="auth.role()==='ADMIN'" (click)="remove(item)">Remove</button>
            </td>
          </tr>
        </table>
      </div>
    </div>
  `
})
export class InventoryComponent {
  api = inject(ApiService);
  toast = inject(ToastService);
  auth = inject(AuthService);
  rows: any[] = [];
  q = '';
  category = '';
  low = false;
  loading = true;
  error = '';
  show = false;
  categories = ['Gold', 'Diamond', 'Silver', 'Platinum', 'Other'];
  form: any = {sku: '', name: '', category: 'Gold', quantity: 0, purity: '', weight: ''};
  constructor() { this.load(); }
  load() {
    this.loading = true;
    this.error = '';
    const query = new URLSearchParams({page_size: '100'});
    if (this.q.trim()) query.set('q', this.q.trim());
    if (this.category) query.set('category', this.category);
    if (this.low) query.set('low_stock', 'true');
    this.api.get<any>('/inventory?' + query.toString()).subscribe({
      next: (page) => { this.rows = page.items; this.loading = false; },
      error: (err) => { this.error = apiMessage(err); this.loading = false; }
    });
  }
  create() {
    this.api.post('/inventory', this.form).subscribe({
      next: () => { this.toast.show('Inventory item saved'); this.show = false; this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
  adjust(item: any, delta: number) {
    this.api.post('/inventory/' + item.id + '/adjust', {delta, reason: delta > 0 ? 'Received stock' : 'Stock correction'}).subscribe({
      next: () => this.load(),
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
  remove(item: any) {
    if (!confirm('Remove ' + item.sku + '?')) return;
    this.api.delete('/inventory/' + item.id).subscribe({
      next: () => { this.toast.show('Inventory item removed'); this.load(); },
      error: (err) => this.toast.show(apiMessage(err))
    });
  }
}
