import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute, Router, RouterLink} from '@angular/router';
import {ApiService, apiMessage} from '../../core/api.service';
import {digitsOnly, PHONE_HINT, validIndianMobile} from '../../core/phones';
import {moveSuggest, suggestNav} from '../../core/suggest-keys';
import {ToastService} from '../../core/toast.service';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <h1>Create order</h1>
    <p class="lead">Choose a customer and add every piece on the job card</p>
    <form (ngSubmit)="save()">
      <article class="card">
        <div class="row">
          <label class="field suggest">Customer
            <input class="input" [(ngModel)]="customerQuery" name="customer" placeholder="Type a name or mobile number" autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="suggestOpen && !newCustomer" [disabled]="newCustomer" (ngModelChange)="suggestCustomers()" (focus)="suggestCustomers()" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, !newCustomer && suggestOpen ? suggestions : [], chooseCustomer, closeList)">
            <ul class="suggest-list" role="listbox" *ngIf="!newCustomer && suggestOpen && suggestions.length">
              <li *ngFor="let customer of suggestions; let i = index">
                <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="pickCustomer(customer)">
                  {{customer.name}}
                  <small>{{customer.phone}}</small>
                </button>
              </li>
            </ul>
          </label>
          <label><input type="checkbox" [(ngModel)]="newCustomer" name="new"> New customer</label>
        </div>
        <div class="row" *ngIf="newCustomer" style="margin-top:10px">
          <label class="field suggest">Name
            <input class="input" [(ngModel)]="person.name" name="pname" placeholder="Name" required autocomplete="off" role="combobox" aria-autocomplete="list" [attr.aria-expanded]="suggestOpen" (ngModelChange)="suggestNewName()" (focus)="suggestNewName()" (blur)="hideSoon()" (keydown)="moveSuggest($event, nav, suggestions, chooseCustomer, closeList)">
            <ul class="suggest-list" role="listbox" *ngIf="suggestOpen && suggestions.length">
              <li *ngFor="let customer of suggestions; let i = index">
                <button type="button" role="option" [class.active]="i===nav.active" [attr.aria-selected]="i===nav.active" (mouseenter)="nav.active=i" (mousedown)="$event.preventDefault()" (click)="pickCustomer(customer)">
                  {{customer.name}}
                  <small>existing customer · {{customer.phone}}</small>
                </button>
              </li>
            </ul>
          </label>
          <label class="field">Mobile
            <input class="input" [ngModel]="person.phone" (ngModelChange)="setNewPhone($event)" name="pphone" required inputmode="numeric" maxlength="10">
            <span class="phone-hint" *ngIf="!validIndianMobile(person.phone)">{{phoneHint}}</span>
            <span class="existing" *ngIf="existingCustomer">existing customer · {{existingCustomer.name}}</span>
          </label>
          <label><input type="checkbox" [(ngModel)]="person.whatsapp_opt_in" name="opt"> WhatsApp</label>
        </div>
        <div class="row" style="margin-top:10px">
          <label class="field">Expected completion<input class="input" type="date" [(ngModel)]="expected" name="expected"></label>
          <label class="field" style="flex:1">Notes<input class="input" [(ngModel)]="notes" name="notes"></label>
        </div>
      </article>
      <article class="card" style="margin-top:12px" *ngFor="let item of items; let i = index">
        <div class="row">
          <select class="input" [(ngModel)]="item.item_type" [name]="'type'+i">
            <option *ngFor="let type of types" [value]="type">{{type}}</option>
          </select>
          <input class="input" [(ngModel)]="item.description" [name]="'desc'+i" placeholder="Description">
          <input class="input" type="number" min="1" [(ngModel)]="item.quantity" [name]="'qty'+i" placeholder="Qty">
          <input class="input" type="number" min="0" [(ngModel)]="item.estimated_value" [name]="'val'+i" placeholder="Estimate">
          <select class="input" [(ngModel)]="item.inventory_item_id" [name]="'sku'+i">
            <option [ngValue]="null">No inventory link</option>
            <option *ngFor="let stock of inventory" [ngValue]="stock.id">{{stock.sku}} — {{stock.name}} ({{stock.available_quantity}} free)</option>
          </select>
          <button class="btn secondary" type="button" (click)="remove(i)" [disabled]="items.length===1">Remove</button>
        </div>
      </article>
      <div class="actions" style="margin-top:12px">
        <button class="btn secondary" type="button" (click)="add()">Add item</button>
        <button class="btn" type="submit" [disabled]="saving">Save order</button>
        <a routerLink="/orders">Cancel</a>
      </div>
      <p class="error-box" *ngIf="error">{{error}}</p>
    </form>
  `
})
export class OrderFormComponent {
  api = inject(ApiService);
  router = inject(Router);
  route = inject(ActivatedRoute);
  toast = inject(ToastService);
  inventory: any[] = [];
  customerId = '';
  customerQuery = '';
  suggestions: any[] = [];
  suggestOpen = false;
  nav = suggestNav();
  moveSuggest = moveSuggest;
  chooseCustomer = (customer: any) => this.pickCustomer(customer);
  closeList = () => { this.suggestOpen = false; this.nav.active = -1; };
  private suggestTimer: any;
  private selectedLabel = '';
  private ignoreSuggest = false;
  newCustomer = false;
  person = {name: '', phone: '', whatsapp_opt_in: false};
  phoneHint = PHONE_HINT;
  digitsOnly = digitsOnly;
  validIndianMobile = validIndianMobile;
  existingCustomer: any = null;
  setNewPhone(value: string) {
    this.person.phone = digitsOnly(value);
    this.existingCustomer = null;
    if (!validIndianMobile(this.person.phone)) return;
    this.api.get<any>('/customers?page_size=8&q=' + encodeURIComponent(this.person.phone)).subscribe({
      next: (page) => { this.existingCustomer = (page.items || []).find((customer: any) => customer.phone === this.person.phone) || null; }
    });
  }
  expected = '';
  notes = '';
  saving = false;
  error = '';
  types = ['Ring', 'Chain', 'Bangle', 'Earring', 'Pendant', 'Necklace', 'Bracelet', 'Dollar', 'Diamond Ring', 'Other'];
  items: any[] = [{item_type: 'Ring', description: '', quantity: 1, estimated_value: null, inventory_item_id: null}];
  constructor() {
    const preset = this.route.snapshot.queryParamMap.get('customer') || '';
    if (preset) {
      this.customerId = preset;
      this.api.get<any>('/customers/' + preset).subscribe({
        next: (customer) => {
          this.ignoreSuggest = true;
          this.selectedLabel = customer.name + ' — ' + customer.phone;
          this.customerQuery = this.selectedLabel;
        },
        error: (err) => this.error = apiMessage(err)
      });
    }
    this.api.get<any>('/inventory?page_size=100').subscribe({next: (page) => this.inventory = page.items});
  }
  suggestCustomers() {
    if (this.ignoreSuggest) { this.ignoreSuggest = false; return; }
    if (this.newCustomer) return;
    if (this.customerId && this.customerQuery === this.selectedLabel) return;
    this.customerId = '';
    this.lookup(this.customerQuery);
  }
  suggestNewName() { this.lookup(this.person.name); }
  lookup(raw: string) {
    clearTimeout(this.suggestTimer);
    const term = (raw || '').trim();
    if (term.length < 1) { this.suggestions = []; this.suggestOpen = false; this.nav.active = -1; return; }
    this.suggestTimer = setTimeout(() => {
      this.api.get<any>('/customers?page_size=8&q=' + encodeURIComponent(term)).subscribe({
        next: (page) => { this.nav.active = -1; this.suggestions = page.items || []; this.suggestOpen = this.suggestions.length > 0; }
      });
    }, 180);
  }
  pickCustomer(customer: any) {
    this.ignoreSuggest = true;
    this.customerId = String(customer.id);
    this.selectedLabel = customer.name + ' — ' + customer.phone;
    this.customerQuery = this.selectedLabel;
    this.newCustomer = false;
    this.suggestOpen = false;
    this.suggestions = [];
  }
  hideSoon() { setTimeout(() => this.suggestOpen = false, 160); }
  add() { this.items.push({item_type: 'Chain', description: '', quantity: 1, estimated_value: null, inventory_item_id: null}); }
  remove(index: number) { this.items.splice(index, 1); }
  save() {
    this.saving = true;
    this.error = '';
    const body: any = {
      expected_delivery_date: this.expected || null,
      notes: this.notes || null,
      items: this.items.map((item) => ({...item, estimated_value: item.estimated_value === '' || item.estimated_value === null ? null : Number(item.estimated_value), inventory_item_id: item.inventory_item_id || null}))
    };
    if (this.newCustomer) {
      if (!String(this.person.name || '').trim() || !validIndianMobile(this.person.phone) || this.existingCustomer) { this.saving = false; return; }
      body.new_customer = this.person;
    }
    else if (!this.customerId) { this.error = 'Choose a customer from the suggestions, or add a new one.'; this.saving = false; return; }
    else body.customer_id = Number(this.customerId);
    this.api.post<any>('/orders', body).subscribe({
      next: (order) => { this.toast.show('Order ' + order.order_number + ' saved'); this.router.navigate(['/orders', order.id]); },
      error: (err) => { this.error = apiMessage(err); this.saving = false; }
    });
  }
}
